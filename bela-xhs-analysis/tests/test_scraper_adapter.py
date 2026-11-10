"""Tests for scraper_adapter.py."""
from scripts.library.scraper_adapter import (
    adapt_profile_notes, adapt_single_note,
    _extract_user_id, _build_note_url,
)


def test_adapt_profile_basic():
    user_info = {
        "nickname": "姜饼探AI", "redId": "95475810861",
        "desc": "北邮", "ip": "北京",
    }
    raw_notes = [
        {"title": "GitHub 三步上手", "type": "normal",
         "likes": "3.1万", "xsecToken": "TOKEN1", "noteId": "abc123"},
        {"title": "Claude.md 怎么写", "type": "video",
         "likes": "654", "xsecToken": "TOKEN2", "noteId": "def456"},
    ]
    profile_url = "https://www.xiaohongshu.com/user/profile/672bcca5?xsec_token=X"

    out = adapt_profile_notes(user_info, raw_notes, profile_url=profile_url)

    assert out["blogger"]["name"] == "姜饼探AI"
    assert out["blogger"]["redId"] == "95475810861"
    assert out["blogger"]["userId"] == "672bcca5"
    assert out["blogger"]["profile_url"] == profile_url
    assert out["blogger"]["fans"] is None  # 标 None，不编造

    assert len(out["notes"]) == 2
    n0 = out["notes"][0]
    assert n0["title"] == "GitHub 三步上手"
    assert n0["likes"] == 31000  # 3.1万 解析
    assert n0["format"] == "图文"
    assert "TOKEN1" in n0["url"]
    assert n0["date"] is None
    assert n0["collects"] is None

    n1 = out["notes"][1]
    assert n1["format"] == "视频"
    assert n1["likes"] == 654


def test_adapt_handles_empty_notes():
    out = adapt_profile_notes({"nickname": "x"}, [])
    assert out["notes"] == []


def test_extract_user_id_from_url():
    url = "https://www.xiaohongshu.com/user/profile/672bcca5000000001c01bfed?xsec_token=X"
    assert _extract_user_id(url) == "672bcca5000000001c01bfed"


def test_extract_user_id_handles_missing():
    assert _extract_user_id("") == ""
    assert _extract_user_id("https://xhs.com/somewhere") == ""


def test_build_note_url():
    url = _build_note_url("abc123", "TOKEN")
    assert "abc123" in url
    assert "xsec_token=TOKEN" in url


def test_adapt_single_note_basic():
    raw = {
        "noteCard": {
            "displayTitle": "测试笔记",
            "type": "normal",
            "interactInfo": {
                "likedCount": "1.5万",
                "collectedCount": "200",
                "commentCount": "30",
            },
            "tagList": [{"name": "AI"}, {"name": "工具"}],
        },
        "url": "https://x.com/discovery/item/abc?xsec_token=T",
    }
    out = adapt_single_note(raw)
    assert out["title"] == "测试笔记"
    assert out["likes"] == 15000
    assert out["collects"] == 200
    assert out["comments"] == 30
    assert out["format"] == "图文"
    assert "AI" in out["tags"]
    assert out["url"].startswith("https://x.com")
