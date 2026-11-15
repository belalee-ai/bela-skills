# -*- coding: utf-8 -*-
"""
处理记录缓存 —— 避免对同一文件做重复 API 调用，节省配额。

缓存文件：~/.tiny-png-cache.json
缓存键：file_sha256 + operation_signature（+ 可选 preset/mime）
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from threading import Lock

CACHE_PATH = Path.home() / ".tiny-png-cache.json"
_save_lock = Lock()
_modify_lock = Lock()
MAX_CACHE_ENTRIES = 10000


def _empty():
    return {"version": 1, "entries": {}}


def load_cache():
    if not CACHE_PATH.exists():
        return _empty()
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") != 1 or "entries" not in data:
            return _empty()
        return data
    except (json.JSONDecodeError, OSError):
        return _empty()


def save_cache(cache):
    """写盘（线程安全 + 0o600 权限）。"""
    with _save_lock:
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            try:
                os.chmod(CACHE_PATH, 0o600)
            except OSError:
                pass
        except OSError:
            pass


def file_sha256(path, chunk_size=64 * 1024):
    """计算文件内容的 SHA-256（按内容判重，文件移动/重命名也能识别）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def operation_signature(opts):
    """
    把当前命令的所有"会改变输出"的参数组合成一个字符串。
    相同参数组合 → 相同签名 → 可命中缓存。
    """
    parts = []
    if opts.get("resize_method"):
        w = opts.get("width") or "_"
        h = opts.get("height") or "_"
        parts.append(f"r={opts['resize_method']}({w}x{h})")
    if opts.get("background"):
        parts.append(f"bg={opts['background']}")
    if opts.get("preserve_fields"):
        parts.append("m=" + ",".join(sorted(opts["preserve_fields"])))
    return "|".join(parts) or "compress"


def make_cache_key(file_hash, op_sig, preset_name=None, mime=None):
    """key 包含文件指纹 + 操作签名 + 当前任务的 preset / mime。"""
    extras = ""
    if preset_name:
        extras += f"#preset={preset_name}"
    if mime:
        extras += f"#mime={mime}"
    return f"{file_hash}|{op_sig}{extras}"


def is_cached(cache, key, output_path=None):
    """
    命中条件：
    - key 在缓存中
    - 如果指定了 output_path，要求该路径仍然存在（否则缓存视为过期）
    """
    entry = cache.get("entries", {}).get(key)
    if not entry:
        return False
    if output_path is not None:
        if not Path(entry.get("output_path", "")).exists():
            return False
    return True


def get_cached(cache, key):
    return cache.get("entries", {}).get(key)


def add_entry(cache, key, input_path, output_path, size_before, size_after):
    """线程安全地写入一条缓存。"""
    with _modify_lock:
        cache.setdefault("entries", {})[key] = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "size_before": int(size_before),
            "size_after": int(size_after),
            "processed_at": datetime.now().isoformat(timespec="seconds"),
        }


def prune(cache, max_entries=MAX_CACHE_ENTRIES):
    """超过 max_entries 时按 processed_at 降序保留最新。"""
    entries = cache.get("entries", {})
    if len(entries) <= max_entries:
        return
    sorted_items = sorted(
        entries.items(),
        key=lambda kv: kv[1].get("processed_at", ""),
        reverse=True,
    )
    cache["entries"] = dict(sorted_items[:max_entries])


def stats(cache):
    """返回 (条目数, 累计节省字节数)。"""
    entries = cache.get("entries", {})
    total = len(entries)
    saved = sum(
        max(0, e.get("size_before", 0) - e.get("size_after", 0))
        for e in entries.values()
    )
    return {"count": total, "saved_bytes": saved}
