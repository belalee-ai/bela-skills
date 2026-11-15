#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bela-tiny-png : TinyPNG 图片批量处理工具（主入口）

支持的能力：
  • 智能压缩（含 HEIC/HEIF iPhone 拍摄格式自动转 JPEG）
  • 智能缩放（4 种算法 scale/fit/cover/thumb）
  • 16 个社交平台预设（小红书/微信/IG/Twitter/微博/抖音 等）
  • 一键多尺寸（all-social/xhs-pack/wechat-pack/instagram-pack/twitter-pack 等）
  • 格式转换（WebP / AVIF / JPEG / PNG / auto）
  • 透明转 JPEG 自动加底色（--background）
  • 保留元数据（copyright / creation / location）
  • 输出独立文件夹（不覆盖原图）+ 终端打印处理汇总（可选写 _report.md）
  • 智能跳过已处理（缓存）+ 跳过已存在输出（--no-overwrite）
  • 并发处理（默认 4 worker）+ ETA 估算
  • 原地模式可选 --backup 保留原图副本
  • 文件过滤（--exclude）+ 超过 Tinify API 限制的超大文件自动跳过
  • Dry-run 预演

调用样例（更多见 SKILL.md）：

    # 工具命令
    python3 compress.py --check-api-key
    python3 compress.py --set-api-key YOUR_KEY
    python3 compress.py --unset-api-key
    python3 compress.py --show-config
    python3 compress.py --list-presets

    # 基础压缩（原地覆盖）
    python3 compress.py /folder

    # 原地覆盖 + 自动备份
    python3 compress.py /folder --backup

    # 输出到独立文件夹 + 排除缩略图
    python3 compress.py /folder --output /out --exclude "*.thumb.*,*-small.*"

    # 多尺寸 + 转 WebP + 串行处理
    python3 compress.py /folder --multi-size all-social --convert webp --workers 1

    # 强制重做（忽略缓存）
    python3 compress.py /folder --preset xiaohongshu --force

退出码：
  0  成功
  1  文件夹不存在
  2  缺少 tinify 库
  3  API key 无效
  4  未配置 API key
  5  缺少必要参数
  6  TinyPNG 账户配额超限
  7  参数错误（非法预设名/格式名/组合冲突）
"""

import argparse
import sys
from pathlib import Path

from api_key import (
    API_CONFIG_PATH, load_api_key, save_api_key, unset_api_key,
    mask_key, show_config,
)
from presets import PRESETS, list_presets_text, resolve_multi_size_arg
from utils import (
    parse_convert_arg, parse_preserve_arg, parse_exclude_arg,
)
from pipeline import run_pipeline


def build_parser():
    parser = argparse.ArgumentParser(
        prog="compress.py",
        description="bela-tiny-png: TinyPNG 批量图片处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="使用 --list-presets 查看所有内置社交平台预设；--show-config 查看当前配置。",
    )

    parser.add_argument("folder", nargs="?", help="需要处理的图片文件夹路径")

    # ───── 工具命令 ─────
    g_tools = parser.add_argument_group("工具命令")
    g_tools.add_argument("--set-api-key", metavar="KEY",
                         help="保存/覆盖 TinyPNG API key 到 ~/.tiny-png-api.json")
    g_tools.add_argument("--unset-api-key", action="store_true",
                         help="删除已保存的 API key（用于切换账号）")
    g_tools.add_argument("--check-api-key", action="store_true",
                         help="检查是否已配置 API key（退出码 0=有，4=无）")
    g_tools.add_argument("--show-config", action="store_true",
                         help="显示当前配置概览（API key + 缓存 + HEIC 支持）")
    g_tools.add_argument("--list-presets", action="store_true",
                         help="列出所有内置预设和组合包")
    g_tools.add_argument("--dry-run", action="store_true",
                         help="预演模式：仅列出将要执行的任务，不调用 API")

    # ───── 输出 ─────
    g_out = parser.add_argument_group("输出")
    g_out.add_argument("--output", metavar="DIR",
                       help="输出文件夹（不指定则原地覆盖；多预设/转格式时自动创建同级目录）")
    g_out.add_argument("--no-overwrite", action="store_true",
                       help="若输出文件已存在则跳过（避免重复覆盖）")
    g_out.add_argument("--backup", action="store_true",
                       help="原地模式下，在 <源>/.tinypng_backup/<时间戳>/ 备份原图")
    g_out.add_argument("--write-report", action="store_true",
                       help="额外生成 <输出文件夹>/_report.md（默认只在终端打印汇总）")

    # ───── 缩放 ─────
    g_resize = parser.add_argument_group("缩放（与 --preset/--multi-size 互斥）")
    g_resize.add_argument(
        "--resize-method", choices=["scale", "fit", "cover", "thumb"],
        help="缩放算法：scale=等比;fit=≤边框;cover=智能裁切;thumb=智能缩略",
    )
    g_resize.add_argument("--width", type=int, help="目标宽度（像素）")
    g_resize.add_argument("--height", type=int, help="目标高度（像素）")

    # ───── Preset ─────
    g_preset = parser.add_argument_group("社交平台预设")
    g_preset.add_argument("--preset",
                          help="单个预设名（用 --list-presets 查看清单）")
    g_preset.add_argument(
        "--multi-size",
        help="多尺寸：bundle 名（如 all-social）或预设逗号列表",
    )

    # ───── Convert ─────
    g_conv = parser.add_argument_group("格式转换")
    g_conv.add_argument(
        "--convert",
        help="目标格式：webp/avif/jpeg/png/auto，可逗号多选（每种 = 1 次 API 调用）",
    )
    g_conv.add_argument(
        "--background",
        help="透明 → JPEG 时的背景色，如 'white' 或 '#FFFFFF'",
    )

    # ───── 元数据 ─────
    g_pres = parser.add_argument_group("元数据")
    g_pres.add_argument(
        "--preserve",
        help="保留字段：copyright/creation/location，可逗号多选或写 'all'",
    )

    # ───── 性能 / 缓存 / 过滤 ─────
    g_perf = parser.add_argument_group("性能 / 缓存 / 过滤")
    g_perf.add_argument(
        "--workers", type=int, default=4, metavar="N",
        help="并发 worker 数（默认 4，写 1 即为串行）",
    )
    g_perf.add_argument(
        "--force", action="store_true",
        help="忽略缓存，强制重新调用 API（用于改了文件但 hash 没变的极端场景）",
    )
    g_perf.add_argument(
        "--exclude", metavar="PATTERN",
        help="跳过匹配的文件名（fnmatch glob，逗号多选，如 '*.thumb.*,*-small.*'）",
    )

    return parser


def auto_output_dir(source_folder, suffix):
    src = Path(source_folder).expanduser()
    return str(src.parent / f"{src.name}_{suffix}")


def validate_args(args):
    """校验参数组合，返回 opts dict。出错时直接 exit。"""

    # 互斥校验
    if args.preset and args.multi_size:
        print("❌ --preset 和 --multi-size 不能同时使用")
        sys.exit(7)
    if args.preset and args.resize_method:
        print("❌ --preset 已自带缩放信息，请勿同时指定 --resize-method")
        sys.exit(7)
    if args.multi_size and args.resize_method:
        print("❌ --multi-size 已自带缩放信息，请勿同时指定 --resize-method")
        sys.exit(7)

    # resize 必填
    if args.resize_method and not (args.width or args.height):
        print("❌ --resize-method 至少需要 --width 或 --height 之一")
        sys.exit(7)
    if args.resize_method in ("cover", "thumb") and not (args.width and args.height):
        print(f"❌ --resize-method {args.resize_method} 必须同时给 --width 和 --height")
        sys.exit(7)

    # 解析 preset
    preset_names = None
    if args.preset:
        if args.preset not in PRESETS:
            print(f"❌ 未知预设：{args.preset}")
            print("   用 --list-presets 查看所有可用预设")
            sys.exit(7)
        preset_names = [args.preset]
    elif args.multi_size:
        names = resolve_multi_size_arg(args.multi_size)
        if names is None or not names:
            print(f"❌ 无效的 --multi-size 参数：{args.multi_size}")
            print("   用 --list-presets 查看所有可用预设和 bundle")
            sys.exit(7)
        preset_names = names

    # 解析 convert
    convert_mimes = None
    if args.convert:
        convert_mimes = parse_convert_arg(args.convert)
        if convert_mimes is None:
            print(f"❌ 无效的 --convert 参数：{args.convert}")
            print("   有效值：webp/avif/jpeg/jpg/png/auto，可逗号多选")
            sys.exit(7)

    # 解析 preserve
    preserve_fields = []
    if args.preserve:
        preserve_fields = parse_preserve_arg(args.preserve)
        if preserve_fields is None:
            print(f"❌ 无效的 --preserve 参数：{args.preserve}")
            print("   有效字段：copyright/creation/location，或写 'all'")
            sys.exit(7)

    # 解析 exclude
    exclude_patterns = parse_exclude_arg(args.exclude) if args.exclude else []

    # workers 范围
    if args.workers < 1 or args.workers > 16:
        print(f"❌ --workers 必须在 1-16 之间，当前 {args.workers}")
        sys.exit(7)

    # background 仅在 convert 时有意义
    if args.background and not convert_mimes:
        print("⚠️  --background 仅在 --convert 时生效，本次将被忽略")

    # backup 仅在原地模式有意义
    if args.backup and args.output:
        print("⚠️  --backup 仅在原地模式（不指定 --output）时生效，本次将被忽略")

    # 自动输出目录（防止意外覆盖原图）
    if not args.output and args.folder:
        if preset_names and len(preset_names) > 1:
            args.output = auto_output_dir(args.folder, "multisize")
            print(f"ℹ️  --multi-size 未指定 --output，自动使用：{args.output}")
        elif preset_names and len(preset_names) == 1:
            args.output = auto_output_dir(args.folder, preset_names[0])
            print(f"ℹ️  --preset 未指定 --output，自动使用：{args.output}")
        elif args.resize_method:
            args.output = auto_output_dir(args.folder, "resized")
            print(f"ℹ️  --resize-method 未指定 --output，自动使用：{args.output}")
        elif convert_mimes:
            tag = "converted" if len(convert_mimes) > 1 else \
                convert_mimes[0].split("/")[-1].replace("*", "auto")
            args.output = auto_output_dir(args.folder, tag)
            print(f"ℹ️  --convert 未指定 --output，自动使用：{args.output}")

    return {
        "preset_names": preset_names,
        "convert_mimes": convert_mimes,
        "preserve_fields": preserve_fields,
        "resize_method": args.resize_method,
        "width": args.width,
        "height": args.height,
        "background": args.background,
        "exclude_patterns": exclude_patterns,
        "workers": args.workers,
        "force": args.force,
        "no_overwrite": args.no_overwrite,
        "backup": args.backup,
        "write_report": args.write_report,
        "dry_run": args.dry_run,
    }


def main():
    parser = build_parser()
    args = parser.parse_args()

    # ───── 工具命令 ─────
    if args.set_api_key:
        save_api_key(args.set_api_key)
        print(f"✅ API key 已保存到 {API_CONFIG_PATH}")
        print(f"   当前 key：{mask_key(args.set_api_key.strip())}")
        return

    if args.unset_api_key:
        if unset_api_key():
            print(f"✅ 已删除 API key 配置：{API_CONFIG_PATH}")
        else:
            print(f"ℹ️  本来就没有 API key 配置：{API_CONFIG_PATH}")
        return

    if args.check_api_key:
        key = load_api_key()
        if key:
            print(f"✅ 已配置 API key：{mask_key(key)}")
            print(f"   配置文件：{API_CONFIG_PATH}")
            sys.exit(0)
        else:
            print(f"⚠️  未在 {API_CONFIG_PATH} 找到 API key 配置")
            print("   👉 请前往 https://tinypng.com/developers 获取后再设置")
            sys.exit(4)

    if args.show_config:
        show_config()
        return

    if args.list_presets:
        print(list_presets_text())
        return

    # ───── 实际处理 ─────
    if not args.folder:
        print("⚠️  请提供需要处理的图片文件夹路径")
        print(f"   用法：python3 {sys.argv[0]} <folder_path> [选项]")
        print(f"   查看选项：python3 {sys.argv[0]} --help")
        print(f"   查看预设：python3 {sys.argv[0]} --list-presets")
        print(f"   查看配置：python3 {sys.argv[0]} --show-config")
        sys.exit(5)

    # 先校验参数（让用户优先看到参数错误）
    opts = validate_args(args)

    # 再检查 API key（dry-run 不需要）
    api_key = load_api_key()
    if not api_key and not args.dry_run:
        print(f"⚠️  未在 {API_CONFIG_PATH} 找到 API key 配置")
        print("\n🔑 请按以下步骤获取 TinyPNG API key：")
        print("   1️⃣  打开 👉 https://tinypng.com/developers")
        print("   2️⃣  填写姓名 + 邮箱，点击 Get your API key")
        print("   3️⃣  收邮件 → 点击邮件中的链接复制 API key")
        print("\n获取后用以下命令保存：")
        print(f"   python3 {sys.argv[0]} --set-api-key YOUR_KEY")
        sys.exit(4)

    run_pipeline(api_key or "DRY_RUN_NO_KEY", args.folder, args.output, opts)


if __name__ == "__main__":
    main()
