"""Tests for meta_store.py."""
import pytest
from scripts.library.meta_store import (
    read_meta, write_meta,
    upsert_note, find_note_by_url, find_note_by_slug,
    append_scan_history,
)


def test_write_and_read_roundtrip(tmp_path, sample_meta):
    meta_file = tmp_path / "_meta.json"
    write_meta(meta_file, sample_meta)
    loaded = read_meta(meta_file)
    assert loaded == sample_meta


def test_read_meta_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_meta(tmp_path / "nope.json")


def test_upsert_note_new(sample_meta):
    note = {
        "file": "notes/2025-11-15-github.md",
        "slug": "github",
        "url": "https://x/1?xsec_token=A",
        "likes": 13, "collects": 2644,
    }
    upsert_note(sample_meta, note)
    assert len(sample_meta["notes_index"]) == 1
    assert sample_meta["notes_index"][0]["slug"] == "github"


def test_upsert_note_update_merges(sample_meta):
    note = {"file": "n.md", "slug": "g", "url": "u1", "likes": 10}
    upsert_note(sample_meta, note)
    note2 = {"slug": "g", "likes": 50, "comments": 5}
    upsert_note(sample_meta, note2)
    assert len(sample_meta["notes_index"]) == 1
    final = sample_meta["notes_index"][0]
    assert final["likes"] == 50
    assert final["comments"] == 5
    # 旧字段保留
    assert final["url"] == "u1"


def test_upsert_note_requires_slug(sample_meta):
    with pytest.raises(ValueError):
        upsert_note(sample_meta, {"url": "x"})


def test_find_note_by_url(sample_meta):
    sample_meta["notes_index"].append({"slug": "a", "url": "https://x/p?xsec_token=A"})
    sample_meta["notes_index"].append({"slug": "b", "url": "https://y/q"})
    assert find_note_by_url(sample_meta, "https://x/p?xsec_token=A")["slug"] == "a"
    assert find_note_by_url(sample_meta, "https://z/r") is None


def test_find_note_ignores_xsec_token(sample_meta):
    """xsec_token 会过期，匹配要忽略它."""
    sample_meta["notes_index"].append({"slug": "a",
        "url": "https://x.com/discovery/item/abc?xsec_token=OLD"})
    found = find_note_by_url(sample_meta,
        "https://x.com/discovery/item/abc?xsec_token=NEW&share_id=X")
    assert found is not None and found["slug"] == "a"


def test_append_scan_history(sample_meta):
    entry = {"date": "2026-05-28T14:30+08:00", "notes_scanned": 5,
             "notes_deep": 2, "new_explosive": 1}
    append_scan_history(sample_meta, entry)
    assert len(sample_meta["scan_history"]) == 1
    assert sample_meta["scan_history"][0]["notes_scanned"] == 5
