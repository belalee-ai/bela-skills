"""增量扫描：对比上次扫描的 _meta.json 与本次 fresh 数据.

设计宪法 C1: 不擅自动手 - 返回 diff，由 caller ask 用户后再执行更新.
"""
from __future__ import annotations


def compute_diff(
    meta: dict,
    fresh_notes: list[dict],
    *,
    fans: int,
    explosive_threshold: int,
    major_pct: float = 0.3,
) -> dict:
    """对比 _meta.json 旧数据 vs fresh 新数据.

    Returns:
        {"new": [slug,...], "major_change": [slug,...],
         "new_explosive": [slug,...], "unchanged_or_minor": [slug,...]}
    """
    old_by_slug = {n["slug"]: n for n in meta.get("notes_index", [])
                   if n.get("status") == "active"}

    new, major, new_explosive, minor = [], [], [], []

    for fn in fresh_notes:
        slug = fn["slug"]
        old = old_by_slug.get(slug)

        if old is None:
            new.append(slug)
            if (fn.get("likes") or 0) >= explosive_threshold:
                new_explosive.append(slug)
            continue

        old_likes = old.get("likes", 0) or 1
        delta = ((fn.get("likes") or 0) - old_likes) / old_likes
        if delta >= major_pct:
            major.append(slug)
        else:
            minor.append(slug)

        if not old.get("is_explosive") and \
                (fn.get("likes") or 0) >= explosive_threshold:
            new_explosive.append(slug)

    return {
        "new": new,
        "major_change": major,
        "new_explosive": new_explosive,
        "unchanged_or_minor": minor,
    }


def summarize_diff(diff: dict) -> str:
    return (
        f"📊 增量摘要：\n"
        f"  · 新发布笔记：{len(diff['new'])} 篇\n"
        f"  · 数据涨幅 ≥30% 的老笔记（大变化）：{len(diff['major_change'])} 篇\n"
        f"  · 新爆文：{len(diff['new_explosive'])} 篇\n"
        f"  · 无大变化：{len(diff['unchanged_or_minor'])} 篇"
    )
