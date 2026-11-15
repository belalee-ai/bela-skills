"""半年外笔记自动归档（不删除）.

设计宪法 C3: 有迹可循 - 老数据物理保留，只是 status=archived 并改 file 路径.
"""
from __future__ import annotations
from datetime import date, timedelta


def should_archive(note_date: date, *, today: date, after_days: int) -> bool:
    return (today - note_date) > timedelta(days=after_days)


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def partition_notes(
    notes: list[dict],
    *,
    today: date,
    after_days: int,
) -> tuple[list[dict], list[dict]]:
    active: list[dict] = []
    to_archive: list[dict] = []
    for n in notes:
        if n.get("status") == "archived":
            continue
        d = _parse_date(n["date"])
        if should_archive(d, today=today, after_days=after_days):
            to_archive.append(n)
        else:
            active.append(n)
    return active, to_archive


def archive_in_meta(
    meta: dict,
    *,
    today: date,
    after_days: int,
) -> list[dict]:
    """将 _meta.json 中半年外的笔记标 archived 并改 file 路径.

    Returns: 被归档的笔记列表（caller 可用于 mv 实际文件）.
    """
    archived = []
    for note in meta.get("notes_index", []):
        if note.get("status") == "archived":
            continue
        # C2: date 缺失时不强行归档（无法判断时间）
        date_str = note.get("date")
        if not date_str or not isinstance(date_str, str):
            continue
        try:
            d = _parse_date(date_str)
        except (ValueError, TypeError):
            continue
        if should_archive(d, today=today, after_days=after_days):
            note["status"] = "archived"
            old = note["file"]
            if "/_archive/" not in old:
                parts = old.split("/")
                note["file"] = "/".join(parts[:-1]) + "/_archive/" + parts[-1]
            archived.append(note)
    return archived
