"""Tests for archive_old.py."""
from datetime import date
from scripts.library.archive_old import (
    should_archive, partition_notes, archive_in_meta,
)


def test_should_archive_old_note():
    today = date(2026, 5, 28)
    old = date(2025, 5, 1)
    assert should_archive(old, today=today, after_days=180) is True


def test_should_not_archive_recent_note():
    today = date(2026, 5, 28)
    recent = date(2026, 4, 1)
    assert should_archive(recent, today=today, after_days=180) is False


def test_partition_notes():
    # today=2026-05-28, after_days=180 → 截止线 ≈ 2025-11-29
    notes = [
        {"slug": "a", "date": "2026-02-01", "status": "active"},  # 116d < 180 → active
        {"slug": "b", "date": "2025-01-01", "status": "active"},  # >> 180 → archive
    ]
    active, to_archive = partition_notes(
        notes, today=date(2026, 5, 28), after_days=180,
    )
    assert [n["slug"] for n in active] == ["a"]
    assert [n["slug"] for n in to_archive] == ["b"]


def test_partition_skips_already_archived():
    notes = [{"slug": "x", "date": "2025-01-01", "status": "archived"}]
    active, to_archive = partition_notes(
        notes, today=date(2026, 5, 28), after_days=180,
    )
    assert active == [] and to_archive == []


def test_archive_in_meta_flips_status(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "old", "file": "notes/old.md",
         "date": "2025-01-01", "status": "active"},
    ]
    archived = archive_in_meta(
        sample_meta, today=date(2026, 5, 28), after_days=180)
    assert len(archived) == 1
    note = sample_meta["notes_index"][0]
    assert note["status"] == "archived"
    assert note["file"] == "notes/_archive/old.md"
