# -*- coding: utf-8 -*-
"""
TinyPNG 图像处理核心管线

负责：
- 验证 API key
- 收集图片（含 HEIC 预转换）
- 展开任务（图片 × 预设 × 目标格式）
- 缓存命中跳过 / 输出已存在跳过 / 超过 API 限制的超大文件跳过
- 备份原图（in-place 模式 + --backup）
- 并发执行（ThreadPoolExecutor）
- 汇总打印 + 可选写 Markdown 报告
"""

import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cache as cache_mod
import heic as heic_mod
import reporter
from presets import PRESETS
from utils import (
    HEIC_EXTENSIONS, NATIVE_EXTENSIONS, TINYPNG_MAX_FILE_SIZE,
    collect_images, safe_relative, mime_to_ext, format_size, is_oversized,
)


# ───── tinify 延迟导入 ─────

def get_tinify():
    try:
        import tinify
        return tinify
    except ImportError:
        print("❌ 缺少 tinify 库")
        print("   请运行： pip install tinify --break-system-packages")
        sys.exit(2)


def validate_api_key(tinify, api_key):
    tinify.key = api_key
    print("🔍 正在验证 TinyPNG API key …")
    try:
        tinify.validate()
    except tinify.AccountError as e:
        print(f"❌ API key 无效或账户异常：{e}")
        print("   请重新前往 https://tinypng.com/developers 获取并 --set-api-key 覆盖")
        sys.exit(3)
    except Exception as e:
        print(f"❌ API key 校验失败：{e}")
        sys.exit(3)
    print("✅ API key 验证通过")


# ───── 输出路径计算 ─────

def compute_output_path(img, rel, src_root, out_root, preset_name, mime,
                        nest_preset_dir=False):
    """
    决定输出文件路径。
    - out_root 为 None：原地，仅基础压缩允许
    - 多预设模式：out_root / preset_name / rel
    - 单预设模式：out_root / rel
    - HEIC 输入：默认输出 .jpg（除非 --convert 指定其它）
    """
    fallback_ext = img.suffix.lower()
    if fallback_ext in HEIC_EXTENSIONS:
        # HEIC 没有目标后缀时默认 .jpg
        fallback_ext = ".jpg"

    new_ext = mime_to_ext(mime, fallback_ext) if mime else fallback_ext

    if out_root is None:
        return img.parent / f"{img.stem}{new_ext}"

    if preset_name and nest_preset_dir:
        target_dir = out_root / preset_name / rel.parent
    else:
        target_dir = out_root / rel.parent

    return target_dir / f"{rel.stem}{new_ext}"


# ───── 任务展开 ─────

def build_jobs(images, source_root, output_root, opts):
    """把图片 × 预设 × 格式扁平化为任务列表。"""
    jobs = []
    preset_names = opts.get("preset_names")
    mime_list = opts.get("convert_mimes")

    presets_iter = preset_names if preset_names else [None]
    mimes_iter = mime_list if mime_list else [None]
    nest_preset_dir = bool(preset_names and len(preset_names) > 1)

    for img in images:
        rel = safe_relative(img, source_root)
        for preset_name in presets_iter:
            for mime in mimes_iter:
                out_path = compute_output_path(
                    img, rel, source_root, output_root, preset_name, mime,
                    nest_preset_dir=nest_preset_dir,
                )
                jobs.append({
                    "input": img,
                    "output": out_path,
                    "preset": preset_name,
                    "mime": mime,
                    "rel": rel,
                })
    return jobs


# ───── HEIC 预处理 ─────

def maybe_convert_heic(img):
    """
    如果是 HEIC：转成临时 JPEG，返回 (临时路径, 是否需要清理)。
    否则返回 (原路径, False)。
    pillow-heif 未安装时，返回 (None, False) 让上游跳过。
    """
    if img.suffix.lower() not in HEIC_EXTENSIONS:
        return img, False

    if not heic_mod.ensure_support():
        return None, False

    try:
        tmp = heic_mod.heic_to_temp_jpeg(img)
        return tmp, True
    except Exception as e:
        print(f"   ❌ HEIC 解析失败：{e}")
        return None, False


# ───── 单任务处理 ─────

def process_one(tinify, job, opts, cache_obj):
    """对一个任务执行 resize → convert → preserve → 写入。"""
    img = job["input"]
    out = job["output"]
    before_size = img.stat().st_size

    # HEIC 预转换
    upload_path, need_cleanup = maybe_convert_heic(img)
    if upload_path is None:
        return {"ok": False, "error_type": "heic-skipped",
                "error": "HEIC 文件需要 pillow-heif 才能处理",
                "before": before_size}

    try:
        source = tinify.from_file(str(upload_path))

        # 1. Resize
        if job["preset"]:
            preset = PRESETS[job["preset"]]
            kwargs = {"method": preset["method"]}
            if preset["width"]:
                kwargs["width"] = preset["width"]
            if preset["height"]:
                kwargs["height"] = preset["height"]
            source = source.resize(**kwargs)
        elif opts.get("resize_method"):
            kwargs = {"method": opts["resize_method"]}
            if opts.get("width"):
                kwargs["width"] = opts["width"]
            if opts.get("height"):
                kwargs["height"] = opts["height"]
            source = source.resize(**kwargs)

        # 2. Convert
        if job["mime"]:
            source = source.convert(type=job["mime"])
            if opts.get("background"):
                source = source.transform(background=opts["background"])

        # 3. Preserve
        if opts.get("preserve_fields"):
            source = source.preserve(*opts["preserve_fields"])

        # 4. 写入
        out.parent.mkdir(parents=True, exist_ok=True)
        source.to_file(str(out))

        after_size = out.stat().st_size

        # 写缓存（用 input 文件 hash，便于跨次识别）
        try:
            file_hash = cache_mod.file_sha256(img)
            op_sig = cache_mod.operation_signature(opts)
            ck = cache_mod.make_cache_key(file_hash, op_sig,
                                          job["preset"], job["mime"])
            cache_mod.add_entry(cache_obj, ck, img, out, before_size, after_size)
        except Exception:
            pass

        return {"ok": True, "before": before_size, "after": after_size}

    except tinify.AccountError as e:
        return {"ok": False, "error_type": "account",
                "error": str(e), "before": before_size}
    except tinify.ClientError as e:
        return {"ok": False, "error_type": "client",
                "error": str(e), "before": before_size}
    except tinify.ServerError as e:
        return {"ok": False, "error_type": "server",
                "error": str(e), "before": before_size}
    except tinify.ConnectionError as e:
        return {"ok": False, "error_type": "connection",
                "error": str(e), "before": before_size}
    except Exception as e:
        return {"ok": False, "error_type": "unknown",
                "error": str(e), "before": before_size}
    finally:
        if need_cleanup and upload_path and upload_path.exists():
            try:
                upload_path.unlink()
            except OSError:
                pass


# ───── 备份（in-place 模式）─────

def backup_originals(images, source_root):
    """把原图复制到 <source>/.tinypng_backup/<timestamp>/。返回备份目录路径。"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = source_root / ".tinypng_backup" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    for img in images:
        rel = safe_relative(img, source_root)
        target = backup_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img, target)
    return backup_dir


# ───── 主流程 ─────

def run_pipeline(api_key, source_folder, output_folder, opts):
    tinify = get_tinify()
    dry_run = opts.get("dry_run", False)
    workers = max(1, int(opts.get("workers", 4)))
    use_cache = not opts.get("force", False)
    no_overwrite = opts.get("no_overwrite", False)
    backup = opts.get("backup", False)
    write_report = opts.get("write_report", False)
    exclude_patterns = opts.get("exclude_patterns") or []

    if not dry_run:
        validate_api_key(tinify, api_key)
    else:
        print("🧪 [Dry Run 模式] 仅展示计划，不会调用 TinyPNG API")

    # 准备路径
    folder = Path(source_folder).expanduser()
    if not folder.exists() or not folder.is_dir():
        print(f"❌ 文件夹不存在或不是目录：{folder}")
        sys.exit(1)

    out_root = Path(output_folder).expanduser() if output_folder else None

    print(f"\n📁 目标文件夹：{folder}")
    if out_root:
        print(f"📂 输出文件夹：{out_root}")
    else:
        print("📂 输出模式：⚠️ 原地覆盖（会修改原文件）")
    if exclude_patterns:
        print(f"🚫 排除模式：{', '.join(exclude_patterns)}")
    if workers > 1 and not dry_run:
        print(f"⚡ 并发 worker：{workers}")
    if use_cache:
        print("💾 启用处理缓存（已处理过的相同操作会跳过；用 --force 强制重做）")

    # 收集图片
    print("🔎 正在扫描图片 …")
    images = collect_images(folder, exclude_patterns=exclude_patterns)
    if not images:
        print("⚠️  没有找到可处理的图片")
        return

    # HEIC 检测与提示
    heic_files = [img for img in images if img.suffix.lower() in HEIC_EXTENSIONS]
    if heic_files:
        if not heic_mod.ensure_support():
            print(f"\n{heic_mod.install_hint()}")
            print(f"   本次将跳过 {len(heic_files)} 个 HEIC 文件\n")
            images = [img for img in images if img.suffix.lower() in NATIVE_EXTENSIONS]
        else:
            print(f"📷 发现 {len(heic_files)} 个 HEIC/HEIF 文件，将自动转 JPEG 后处理")

    # 大小过滤（超过 Tinify API 单文件限制时跳过）
    oversized = [img for img in images if is_oversized(img)]
    if oversized:
        print(f"\n📦 跳过 {len(oversized)} 个超过 {format_size(TINYPNG_MAX_FILE_SIZE)} "
              f"的文件（Tinify API 单文件上限）：")
        for f in oversized[:5]:
            print(f"   • {f.name} ({format_size(f.stat().st_size)})")
        if len(oversized) > 5:
            print(f"   …（共 {len(oversized)} 个）")
        images = [img for img in images if not is_oversized(img)]

    if not images:
        print("\n⚠️  过滤后没有可处理的图片")
        return

    # 展开任务
    jobs = build_jobs(images, folder, out_root, opts)
    print(f"\n🖼️  待处理图片：{len(images)} 张 → {len(jobs)} 个输出任务")

    # 缓存命中预扫描
    cache_obj = cache_mod.load_cache()
    cached_hits = 0
    skipped_existing = 0
    pending_jobs = []
    for job in jobs:
        # 缓存检查
        if use_cache:
            try:
                file_hash = cache_mod.file_sha256(job["input"])
                op_sig = cache_mod.operation_signature(opts)
                ck = cache_mod.make_cache_key(file_hash, op_sig,
                                              job["preset"], job["mime"])
                if cache_mod.is_cached(cache_obj, ck, job["output"]):
                    cached_hits += 1
                    continue
            except Exception:
                pass
        # --no-overwrite
        if no_overwrite and job["output"].exists():
            skipped_existing += 1
            continue
        pending_jobs.append(job)

    if cached_hits:
        print(f"💾 缓存命中：{cached_hits} 个任务已处理过，将跳过（节省 {cached_hits} 次 API 调用）")
    if skipped_existing:
        print(f"⏭️  --no-overwrite：{skipped_existing} 个输出已存在，将跳过")

    if not pending_jobs:
        print("\n🎉 所有任务都已完成（缓存命中或输出已存在），无需调用 API")
        return

    # 配额检查
    monthly_used = None
    if not dry_run:
        try:
            monthly_used = tinify.compression_count
            remaining = max(0, 500 - monthly_used)
            print(f"\n📊 当月已用 TinyPNG 次数：{monthly_used}/500（剩余 {remaining}）")
            if len(pending_jobs) > remaining:
                print(f"⚠️  警告：本次需 {len(pending_jobs)} 次调用，剩余仅 {remaining} 次，可能中途超限")
            elif len(pending_jobs) > 100:
                print(f"⚠️  本次将消耗 {len(pending_jobs)} 次 API 调用，请留意配额")
        except Exception:
            pass

    print("=" * 70)

    # Dry run：只打印计划
    if dry_run:
        for i, job in enumerate(pending_jobs, 1):
            ops = []
            if job["preset"]:
                p = PRESETS[job["preset"]]
                h = p["height"] or "auto"
                ops.append(f"resize→{job['preset']}({p['width']}×{h},{p['method']})")
            elif opts.get("resize_method"):
                ops.append(
                    f"resize→{opts['resize_method']}"
                    f"({opts.get('width') or '?'}×{opts.get('height') or '?'})"
                )
            if job["mime"]:
                ops.append(f"convert→{job['mime']}")
            if opts.get("preserve_fields"):
                ops.append(f"preserve({','.join(opts['preserve_fields'])})")
            if not ops:
                ops.append("compress only")
            heic_tag = "  [HEIC→JPEG]" if job["input"].suffix.lower() in HEIC_EXTENSIONS else ""
            print(f"[{i}/{len(pending_jobs)}] {job['rel']}{heic_tag}")
            print(f"   → {job['output']}")
            print(f"   ops: {' → '.join(ops)}")
        print(f"\n🧪 Dry run 完成。实际执行将消耗约 {len(pending_jobs)} 次 API 调用")
        return

    # in-place + 备份
    if out_root is None and backup:
        backup_targets = list({job["input"] for job in pending_jobs})
        backup_dir = backup_originals(backup_targets, folder)
        print(f"💼 已备份 {len(backup_targets)} 个原图到：{backup_dir}")

    # 并发执行
    progress = reporter.ProgressTracker(len(pending_jobs))
    results_by_idx = {}
    abort_event = threading.Event()
    start_time = time.time()
    quota_exceeded = False

    def worker(idx, job):
        if abort_event.is_set():
            return idx, {"ok": False, "error_type": "aborted",
                         "error": "上游配额错误已中止",
                         "before": job["input"].stat().st_size}
        return idx, process_one(tinify, job, opts, cache_obj)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(worker, idx, job)
            for idx, job in enumerate(pending_jobs)
        ]
        for fut in as_completed(futures):
            try:
                idx, res = fut.result()
            except Exception as e:
                # 工作线程意外异常
                continue
            results_by_idx[idx] = res

            job = pending_jobs[idx]
            rel = job["rel"]

            # 单任务输出 block
            tags = []
            if job["preset"]:
                tags.append(f"📐 {job['preset']}")
            if job["mime"] and job["mime"] != "image/*":
                tags.append(f"🔄 {mime_to_ext(job['mime'], '').lstrip('.')}")
            elif job["mime"] == "image/*":
                tags.append("🔄 auto")
            if job["input"].suffix.lower() in HEIC_EXTENSIONS:
                tags.insert(0, "📷 HEIC")

            display_name = f"{rel}" + (f"  [{', '.join(tags)}]" if tags else "")
            before_size = res["before"]

            block_lines = [f"🔄 {display_name}", f"📤 原始：{format_size(before_size)}"]

            if res["ok"]:
                ratio = (1 - res["after"] / before_size) * 100 if before_size else 0
                block_lines.append(
                    f"✅ → {job['output'].name}（{format_size(res['after'])}, 减少 {ratio:.1f}%）"
                )
            elif res["error_type"] == "account":
                block_lines.append(f"❌ 账户错误：{res['error']}")
                block_lines.append("⛔ 已中止后续任务（可能配额用完）")
                abort_event.set()
                quota_exceeded = True
            elif res["error_type"] == "aborted":
                block_lines.append("⏸️  已跳过（上游配额错误）")
            else:
                block_lines.append(f"❌ {res['error_type']}: {res['error']}")

            completed, elapsed_str, eta_str = progress.step()
            reporter.print_image_block(
                completed, len(pending_jobs), block_lines,
                completed=completed, elapsed=elapsed_str, eta=eta_str,
            )

    # 整理结果（按原始顺序）
    results = []
    total_before = 0
    total_after = 0
    for idx, job in enumerate(pending_jobs):
        res = results_by_idx.get(idx)
        if not res:
            continue
        rel = job["rel"]
        tags = []
        if job["preset"]:
            tags.append(job["preset"])
        if job["mime"]:
            ext = mime_to_ext(job["mime"], "").lstrip(".") or "auto"
            tags.append(ext)
        display_name = f"{rel}" + (f"  [{', '.join(tags)}]" if tags else "")

        before = res["before"]
        total_before += before

        if res["ok"]:
            after = res["after"]
            total_after += after
            ratio = (1 - after / before) * 100 if before else 0
            results.append({
                "name": display_name, "before": before, "after": after,
                "ratio": ratio, "status": "✅",
            })
        elif res["error_type"] == "account":
            total_after += before
            results.append({
                "name": display_name, "before": before, "after": before,
                "ratio": 0, "status": "❌ 配额",
            })
        elif res["error_type"] == "aborted":
            total_after += before
            results.append({
                "name": display_name, "before": before, "after": before,
                "ratio": 0, "status": "⏸️ 跳过",
            })
        else:
            total_after += before
            results.append({
                "name": display_name, "before": before, "after": before,
                "ratio": 0, "status": "❌",
            })

    # 配额读取最终值
    try:
        monthly_used = tinify.compression_count
    except Exception:
        pass

    elapsed_total = time.time() - start_time
    reporter.print_summary_table(
        results, total_before, total_after,
        monthly_used=monthly_used,
        elapsed_seconds=elapsed_total,
        skipped_oversized=len(oversized) if oversized else None,
        cached_hits=cached_hits if cached_hits else None,
    )

    # 默认只打印汇总；用户显式加 --write-report 时才写报告文件。
    if write_report and out_root and results:
        report_path = out_root / "_report.md"
        try:
            reporter.write_report(
                report_path, results, total_before, total_after,
                folder, out_root, opts,
                monthly_used=monthly_used,
                elapsed_seconds=elapsed_total,
                cached_hits=cached_hits,
                skipped_oversized=len(oversized),
            )
            print(f"\n📝 报告已生成：{report_path}")
        except Exception as e:
            print(f"\n⚠️  报告写入失败：{e}")
    elif write_report and not out_root:
        print("\n⚠️  --write-report 需要配合 --output 使用，本次只打印终端汇总")

    # 持久化缓存
    try:
        cache_mod.prune(cache_obj)
        cache_mod.save_cache(cache_obj)
    except Exception:
        pass

    if quota_exceeded:
        print("\n⚠️  本次因配额超限提前终止，请下月再试或升级账户")
        sys.exit(6)

    print("\n🎉 全部完成！")
