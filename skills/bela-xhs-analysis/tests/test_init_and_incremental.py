"""Tests for init_blogger.py + incremental_scan.py."""
from datetime import date
from scripts.library.init_blogger import (
    init_blogger_dirs, compute_threshold, build_meta,
)
from scripts.library.incremental_scan import (
    compute_diff, summarize_diff,
)


# init_blogger ---

def test_init_creates_full_tree(tmp_path):
    bdir = tmp_path / "test-blogger"
    init_blogger_dirs(bdir)
    assert (bdir / "notes" / "_archive").is_dir()
    assert (bdir / "images" / "covers").is_dir()
    assert (bdir / "images" / "slides").is_dir()


def test_compute_threshold_low_fans():
    assert compute_threshold(fans=1500, fans_threshold=2000,
                             low=1000, high=5000) == 1000


def test_compute_threshold_high_fans():
    assert compute_threshold(fans=15000, fans_threshold=2000,
                             low=1000, high=5000) == 5000


def test_build_meta_structure():
    meta = build_meta(
        {"name": "姜饼探AI", "redId": "X", "userId": "Y",
         "fans": 15000, "profile_url": "https://..."},
        industry="AI工具", is_target=True,
        threshold=5000, today=date(2026, 5, 28),
    )
    assert meta["schema_version"] == "1.0"
    assert meta["blogger"]["platform"] == "xhs"
    assert meta["blogger"]["name"] == "姜饼探AI"
    assert meta["blogger"]["industry"] == "AI工具"
    assert meta["blogger"]["is_target"] is True
    assert meta["explosive_threshold"] == 5000
    assert meta["blogger"]["first_seen"] == "2026-05-28"
    assert meta["scan_history"] == []
    assert meta["notes_index"] == []
    assert meta["blogger"]["fans_count_history"][0]["count"] == 15000


def test_build_meta_handles_none_fans():
    meta = build_meta(
        {"name": "x", "fans": None}, industry="AI工具",
        is_target=True, threshold=5000, today=date(2026, 5, 28),
    )
    assert meta["blogger"]["fans_count_history"][0]["count"] == 0


# incremental_scan ---

def test_diff_finds_new_notes(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "old", "date": "2025-10-01", "likes": 100,
         "collects": 50, "is_explosive": False, "status": "active"},
    ]
    fresh = [
        {"slug": "old", "likes": 105, "collects": 52},
        {"slug": "new", "likes": 1000, "collects": 500},
    ]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                        explosive_threshold=5000)
    assert diff["new"] == ["new"]
    assert "old" in diff["unchanged_or_minor"]


def test_diff_detects_major_growth(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "rising", "likes": 100,
         "is_explosive": False, "status": "active"},
    ]
    fresh = [{"slug": "rising", "likes": 200}]  # 100% 涨幅
    diff = compute_diff(sample_meta, fresh, fans=15000,
                        explosive_threshold=5000, major_pct=0.3)
    assert "rising" in diff["major_change"]


def test_diff_detects_new_explosive(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "x", "likes": 100, "is_explosive": False,
         "status": "active"},
    ]
    fresh = [{"slug": "x", "likes": 8000}]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                        explosive_threshold=5000)
    assert "x" in diff["new_explosive"]


def test_diff_new_note_is_explosive():
    """新发布且达爆文阈值."""
    meta = {"notes_index": []}
    fresh = [{"slug": "new", "likes": 6000}]
    diff = compute_diff(meta, fresh, fans=15000, explosive_threshold=5000)
    assert "new" in diff["new"]
    assert "new" in diff["new_explosive"]


def test_summarize_diff_format():
    diff = {"new": ["a", "b"], "major_change": ["c"],
            "new_explosive": ["a"], "unchanged_or_minor": ["d"]}
    s = summarize_diff(diff)
    assert "新发布笔记：2" in s
    assert "大变化）：1" in s
    assert "新爆文：1" in s
