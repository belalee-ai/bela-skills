"""_meta.json read/write + 索引操作.

设计宪法 C3: 有迹可循 - 所有写入必须保留时间戳和原始 URL.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


_EPHEMERAL_PARAMS = {"xsec_token", "share_id", "shareRedId", "apptime",
                     "xhsshare", "appuid", "app_platform", "app_version"}


def read_meta(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"_meta.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_meta(path: Path, meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _strip_ephemeral(url: str) -> str:
    """归一化 URL（去 xsec_token 等会过期的参数）以做匹配."""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}"


def find_note_by_url(meta: dict, url: str) -> Optional[dict]:
    target = _strip_ephemeral(url)
    for note in meta.get("notes_index", []):
        if "url" in note and _strip_ephemeral(note["url"]) == target:
            return note
    return None


def find_note_by_slug(meta: dict, slug: str) -> Optional[dict]:
    for note in meta.get("notes_index", []):
        if note.get("slug") == slug:
            return note
    return None


def upsert_note(meta: dict, note: dict) -> None:
    """按 slug 去重；存在则覆盖（merge），不存在则追加."""
    slug = note.get("slug")
    if not slug:
        raise ValueError("note must have 'slug' field")
    existing = find_note_by_slug(meta, slug)
    if existing:
        existing.update(note)
    else:
        meta.setdefault("notes_index", []).append(note)


def append_scan_history(meta: dict, entry: dict) -> None:
    meta.setdefault("scan_history", []).append(entry)
