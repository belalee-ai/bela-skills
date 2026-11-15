"""首次入库：建目录树 + 写 _meta.json 骨架.

设计宪法 C1: 不擅自动手 - 不在这里 ASK，caller 负责.
"""
from __future__ import annotations
from pathlib import Path
from datetime import date


def init_blogger_dirs(bdir: Path) -> None:
    """创建博主目录子结构."""
    (bdir / "notes" / "_archive").mkdir(parents=True, exist_ok=True)
    (bdir / "images" / "covers").mkdir(parents=True, exist_ok=True)
    (bdir / "images" / "slides").mkdir(parents=True, exist_ok=True)


def compute_threshold(
    *,
    fans: int,
    fans_threshold: int,
    low: int,
    high: int,
) -> int:
    return low if fans < fans_threshold else high


def build_meta(
    blogger_data: dict,
    *,
    industry: str,
    is_target: bool,
    threshold: int,
    today: date,
) -> dict:
    """构建初始 _meta.json 数据（不含 notes_index）."""
    return {
        "schema_version": "1.0",
        "blogger": {
            "platform": "xhs",
            "name": blogger_data["name"],
            "redId": blogger_data.get("redId", ""),
            "userId": blogger_data.get("userId", ""),
            "industry": industry,
            "is_target": is_target,
            "first_seen": today.isoformat(),
            "fans_count_history": [{
                "date": today.isoformat(),
                "count": blogger_data.get("fans") or 0,
            }],
            "profile_url": blogger_data.get("profile_url", ""),
        },
        "explosive_threshold": threshold,
        "scan_history": [],
        "notes_index": [],
    }
