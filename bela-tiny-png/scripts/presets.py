# -*- coding: utf-8 -*-
"""
社交平台尺寸预设

每个预设包含：
  - width / height：目标尺寸（height=None 表示等比缩放只锁宽度）
  - method：TinyPNG resize 算法（scale/fit/cover/thumb）
    * scale  按比例缩放（只需指定单边）
    * fit    等比缩放到 ≤ 指定宽×高（不裁切）
    * cover  智能裁切到精确尺寸（AI 主体识别）
    * thumb  智能缩略图（AI 主体识别 + 裁切边缘）
  - desc：人类可读说明
"""

PRESETS = {
    # ───── 小红书 ─────
    "xiaohongshu": {
        "width": 1080, "height": 1440, "method": "fit",
        "desc": "小红书竖图 3:4",
    },
    "xiaohongshu-square": {
        "width": 1080, "height": 1080, "method": "fit",
        "desc": "小红书方图 1:1",
    },

    # ───── 微信 ─────
    "wechat-cover": {
        "width": 900, "height": 383, "method": "cover",
        "desc": "公众号封面 2.35:1（智能裁切）",
    },
    "wechat-content": {
        "width": 900, "height": None, "method": "scale",
        "desc": "公众号正文宽 900px（等比缩放）",
    },
    "moments": {
        "width": 1080, "height": 1080, "method": "fit",
        "desc": "微信朋友圈方图 1:1",
    },

    # ───── Instagram ─────
    "instagram-square": {
        "width": 1080, "height": 1080, "method": "fit",
        "desc": "Instagram 方图 1:1",
    },
    "instagram-portrait": {
        "width": 1080, "height": 1350, "method": "fit",
        "desc": "Instagram 竖图 4:5",
    },
    "instagram-story": {
        "width": 1080, "height": 1920, "method": "cover",
        "desc": "Instagram Story / Reels 9:16",
    },

    # ───── Twitter / X ─────
    "twitter-post": {
        "width": 1600, "height": 900, "method": "fit",
        "desc": "Twitter/X 横图 16:9（推文最大显示）",
    },
    "twitter-square": {
        "width": 1080, "height": 1080, "method": "fit",
        "desc": "Twitter/X 方图 1:1",
    },
    "twitter-portrait": {
        "width": 1080, "height": 1350, "method": "fit",
        "desc": "Twitter/X 竖图 4:5",
    },
    "twitter-header": {
        "width": 1500, "height": 500, "method": "cover",
        "desc": "Twitter/X 个人主页头图（智能裁切）",
    },
    "twitter-card": {
        "width": 1200, "height": 628, "method": "cover",
        "desc": "Twitter/X 大图卡片（链接预览）",
    },

    # ───── 微博 / 抖音 ─────
    "weibo": {
        "width": 1242, "height": 1660, "method": "fit",
        "desc": "微博竖图 3:4",
    },
    "douyin": {
        "width": 1080, "height": 1920, "method": "cover",
        "desc": "抖音/快手竖屏 9:16",
    },

    # ───── 缩略图 ─────
    "thumb-300": {
        "width": 300, "height": 300, "method": "thumb",
        "desc": "智能缩略图 300×300（保留主体）",
    },
}


# 预设组合包：一键生成多尺寸（每个预设输出到独立子文件夹）
PRESET_BUNDLES = {
    "all-social": [
        "xiaohongshu", "moments", "instagram-square",
        "instagram-story", "wechat-cover", "twitter-post",
    ],
    "xhs-pack": ["xiaohongshu", "xiaohongshu-square"],
    "wechat-pack": ["wechat-cover", "wechat-content", "moments"],
    "instagram-pack": [
        "instagram-square", "instagram-portrait", "instagram-story",
    ],
    "twitter-pack": [
        "twitter-post", "twitter-square", "twitter-portrait", "twitter-card",
    ],
    "zh-social": [
        "xiaohongshu", "moments", "wechat-cover", "weibo", "douyin",
    ],
    "global-social": [
        "instagram-square", "instagram-story", "twitter-post", "twitter-card",
    ],
}


# ───── 工具函数 ─────

def list_presets_text():
    """返回所有预设的可读列表（用于 `--list-presets`）。"""
    lines = ["📋 bela-tiny-png 预设清单", ""]

    lines.append("【单个预设】（用 --preset NAME）")
    name_w = max(len(n) for n in PRESETS)
    for name, p in PRESETS.items():
        h = p["height"] if p["height"] else "auto"
        size = f"{p['width']}×{h}"
        lines.append(
            f"  {name:<{name_w}}  {size:<14}  [{p['method']:<5}]  {p['desc']}"
        )

    lines.append("")
    lines.append("【组合包 Bundle】（用 --multi-size BUNDLE_NAME）")
    name_w = max(len(n) for n in PRESET_BUNDLES)
    for name, items in PRESET_BUNDLES.items():
        lines.append(f"  {name:<{name_w}}  → {', '.join(items)}")

    lines.append("")
    lines.append("💡 也可以传逗号分隔的预设名作为 --multi-size 参数：")
    lines.append("   --multi-size xiaohongshu,instagram-square,twitter-post")

    return "\n".join(lines)


def resolve_multi_size_arg(arg):
    """
    解析 `--multi-size` 参数：
    - 若为 bundle 名，返回展开后的预设列表
    - 否则按逗号分隔解析为预设名列表
    返回 None 表示存在未知预设名。
    """
    arg = arg.strip()
    if arg in PRESET_BUNDLES:
        return list(PRESET_BUNDLES[arg])

    names = [n.strip() for n in arg.split(",") if n.strip()]
    invalid = [n for n in names if n not in PRESETS]
    if invalid:
        return None
    return names
