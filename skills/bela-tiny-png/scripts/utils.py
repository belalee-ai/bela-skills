# -*- coding: utf-8 -*-
"""
通用工具：
- 支持的图片格式（含 HEIC/HEIF — pipeline 会预处理）
- 字节数格式化
- 递归收集图片 + exclude pattern 过滤
- Tinify API 单文件大小限制
- 命令行参数解析（--convert / --preserve / --exclude）
"""

import fnmatch
from pathlib import Path

# TinyPNG 原生支持 + 我们通过 pillow-heif 间接支持
NATIVE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
HEIC_EXTENSIONS = {".heic", ".heif"}
SUPPORTED_EXTENSIONS = NATIVE_EXTENSIONS | HEIC_EXTENSIONS

# Tinify API 当前单文件大小限制。
# 参考：https://help.tinify.com/help/is-there-a-file-size-limit-for-images
TINYPNG_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


def format_size(size_bytes):
    """字节数 → 人类可读字符串。"""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def collect_images(folder, exclude_patterns=None):
    """
    递归收集所有支持格式的图片，按路径排序。
    可选 exclude_patterns（fnmatch 风格 glob 列表）按文件名（不带路径）过滤。
    """
    exclude_patterns = exclude_patterns or []
    images = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        # 跳过 .tinypng_backup/ 子目录里的原图（不要把备份当成新输入）
        if ".tinypng_backup" in path.parts:
            continue
        # 应用 exclude 模式
        if exclude_patterns and any(
            fnmatch.fnmatch(path.name, p) for p in exclude_patterns
        ):
            continue
        images.append(path)
    images.sort(key=lambda p: str(p).lower())
    return images


def safe_relative(path, root):
    """获取 path 相对 root 的路径，失败时退回文件名。"""
    try:
        return path.relative_to(root)
    except ValueError:
        return Path(path.name)


def is_oversized(path, limit=TINYPNG_MAX_FILE_SIZE):
    """是否超过 Tinify API 单文件大小限制。"""
    try:
        return path.stat().st_size > limit
    except OSError:
        return False


# ───── 格式 / 元数据参数解析 ─────

FORMAT_TO_MIME = {
    "webp": "image/webp",
    "avif": "image/avif",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "auto": "image/*",
}

MIME_TO_EXT = {
    "image/webp": ".webp",
    "image/avif": ".avif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/*": ".img",  # 占位，运行时会被替换
}


def parse_convert_arg(arg):
    """解析 --convert 参数。输入 'webp' 或 'webp,avif'，输出 mime 列表或 None。"""
    if not arg:
        return None
    formats = [f.strip().lower() for f in arg.split(",") if f.strip()]
    mimes = []
    for f in formats:
        if f not in FORMAT_TO_MIME:
            return None
        mimes.append(FORMAT_TO_MIME[f])
    return mimes


VALID_PRESERVE = {"copyright", "creation", "location"}


def parse_preserve_arg(arg):
    """解析 --preserve 参数。'all' 展开为全部三项；非法字段返回 None。"""
    if not arg:
        return []
    if arg.lower() == "all":
        return ["copyright", "creation", "location"]
    fields = [f.strip().lower() for f in arg.split(",") if f.strip()]
    invalid = [f for f in fields if f not in VALID_PRESERVE]
    if invalid:
        return None
    return fields


def parse_exclude_arg(arg):
    """解析 --exclude 参数。逗号分隔的 fnmatch glob 列表。"""
    if not arg:
        return []
    return [p.strip() for p in arg.split(",") if p.strip()]


def mime_to_ext(mime, fallback_ext):
    """MIME → 文件后缀。auto 模式下回退到原后缀。"""
    if mime == "image/*":
        return fallback_ext
    return MIME_TO_EXT.get(mime, fallback_ext)
