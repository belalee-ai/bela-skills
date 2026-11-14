# -*- coding: utf-8 -*-
"""
进度提示 + 结果汇总 + 进度跟踪 + 报告写入
- 并发执行时所有打印必须经过 safe_print（线程安全）
- ProgressTracker 提供 elapsed / ETA 估算
- write_report 把结果写成 Markdown 报告
"""

import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from utils import TINYPNG_MAX_FILE_SIZE, format_size

_print_lock = threading.Lock()


def safe_print(text=""):
    """线程安全的 print（并发执行时避免输出错位）。"""
    with _print_lock:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()


def format_duration(seconds):
    """秒数 → 'm:ss' 或 'h:mm:ss'。"""
    total = int(max(0, seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class ProgressTracker:
    """记录已完成数 + 估算 ETA，线程安全。"""

    def __init__(self, total):
        self.total = total
        self.completed = 0
        self.start_time = time.time()
        self.lock = threading.Lock()

    def step(self):
        """+1 已完成，返回 (completed, elapsed_str, eta_str)。"""
        with self.lock:
            self.completed += 1
            elapsed = time.time() - self.start_time
            if self.completed > 0 and self.completed < self.total:
                avg = elapsed / self.completed
                eta = avg * (self.total - self.completed)
            else:
                eta = 0
            return self.completed, format_duration(elapsed), format_duration(eta)


def print_image_block(idx, total, lines, completed=None, elapsed=None, eta=None):
    """
    把一张图的所有日志合成一个 block 一次性 print，避免并发交错。
    可选追加进度尾巴：[12/50, elapsed 0:35, ETA 2:30]
    """
    head = f"\n[{idx}/{total}]"
    if completed is not None:
        head += f"  ⏱️ 进度 {completed}/{total} | 已用 {elapsed} | 预计还需 {eta}"
    block = "\n".join([head] + ["   " + ln for ln in lines])
    safe_print(block)


def print_summary_table(results, total_before, total_after,
                        monthly_used=None, elapsed_seconds=None,
                        skipped_oversized=None, cached_hits=None):
    """打印 Markdown 汇总表格 + 整体统计。"""
    safe_print("\n" + "=" * 70)
    safe_print("📊 处理结果汇总")
    safe_print("=" * 70 + "\n")

    if not results:
        safe_print("（没有处理任何文件）")
        return

    safe_print("| # | 文件 | 压缩前 | 压缩后 | 压缩率 | 状态 |")
    safe_print("|---|------|-------:|-------:|-------:|:----:|")
    for i, r in enumerate(results, 1):
        safe_print(
            f"| {i} | {r['name']} | "
            f"{format_size(r['before'])} | "
            f"{format_size(r['after'])} | "
            f"{r['ratio']:.1f}% | "
            f"{r['status']} |"
        )

    total_ratio = (1 - total_after / total_before) * 100 if total_before else 0
    saved = total_before - total_after
    safe_print(
        f"\n**📌 合计：{len(results)} 个输出 | "
        f"原图 {format_size(total_before)} → 输出 {format_size(total_after)} | "
        f"节省 {format_size(saved)}（{total_ratio:.1f}%）**"
    )

    extras = []
    if elapsed_seconds is not None:
        extras.append(f"⏱️ 耗时 {format_duration(elapsed_seconds)}")
    if cached_hits:
        extras.append(f"💾 缓存命中 {cached_hits} 张（节省同等数量 API 调用）")
    if skipped_oversized:
        extras.append(
            f"📦 跳过超大文件 {skipped_oversized} 张"
            f"（>{format_size(TINYPNG_MAX_FILE_SIZE)}）"
        )
    if monthly_used is not None:
        extras.append(f"📈 本月 TinyPNG 已用 {monthly_used}/500（免费额度）")

    for line in extras:
        safe_print(line)


def write_report(report_path, results, total_before, total_after,
                 source_folder, output_folder, opts,
                 monthly_used=None, elapsed_seconds=None,
                 cached_hits=0, skipped_oversized=0):
    """生成 Markdown 报告（保存到 output_folder/_report.md）。"""
    lines = []
    lines.append("# bela-tiny-png 处理报告")
    lines.append("")
    lines.append(f"- **时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **源文件夹**：`{source_folder}`")
    if output_folder:
        lines.append(f"- **输出文件夹**：`{output_folder}`")
    lines.append(f"- **输出文件数**：{len(results)}")
    if elapsed_seconds is not None:
        lines.append(f"- **总耗时**：{format_duration(elapsed_seconds)}")
    if cached_hits:
        lines.append(f"- **缓存命中**：{cached_hits} 张（节省 API 调用）")
    if skipped_oversized:
        lines.append(
            f"- **跳过超大文件**：{skipped_oversized} 张"
            f"（>{format_size(TINYPNG_MAX_FILE_SIZE)}）"
        )

    if opts.get("preset_names"):
        lines.append(f"- **预设**：{', '.join(opts['preset_names'])}")
    if opts.get("convert_mimes"):
        lines.append(f"- **格式转换**：{', '.join(opts['convert_mimes'])}")
    if opts.get("preserve_fields"):
        lines.append(f"- **保留元数据**：{', '.join(opts['preserve_fields'])}")
    if opts.get("resize_method"):
        w = opts.get("width") or "auto"
        h = opts.get("height") or "auto"
        lines.append(f"- **缩放**：{opts['resize_method']} {w}×{h}")

    lines.append("")
    lines.append("## 详细列表")
    lines.append("")
    lines.append("| # | 文件 | 压缩前 | 压缩后 | 压缩率 | 状态 |")
    lines.append("|---|------|-------:|-------:|-------:|:----:|")
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['name']} | "
            f"{format_size(r['before'])} | "
            f"{format_size(r['after'])} | "
            f"{r['ratio']:.1f}% | "
            f"{r['status']} |"
        )

    total_ratio = (1 - total_after / total_before) * 100 if total_before else 0
    saved = total_before - total_after
    lines.append("")
    lines.append(
        f"**合计**：原图 {format_size(total_before)} → "
        f"输出 {format_size(total_after)} | "
        f"节省 {format_size(saved)}（{total_ratio:.1f}%）"
    )

    if monthly_used is not None:
        lines.append("")
        lines.append(f"本月已用 TinyPNG 配额：{monthly_used}/500")

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
