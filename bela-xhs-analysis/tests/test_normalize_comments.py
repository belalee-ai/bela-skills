"""Tests for normalize_comments + adapt_profile_complete (S2 新增)."""
from scripts.library.scraper_adapter import (
    normalize_comments, adapt_profile_complete,
)


def test_normalize_v02_format():
    """v0.2.0 输出 {content, likes, nickname} → {text, likes}."""
    raw = [
        {"content": "求教程", "likes": 32, "nickname": "u1"},
        {"content": "码住", "likes": 28, "nickname": "u2"},
    ]
    out = normalize_comments(raw)
    assert len(out) == 2
    assert out[0] == {"text": "求教程", "likes": 32}
    assert out[1] == {"text": "码住", "likes": 28}


def test_normalize_sorts_by_likes_desc():
    raw = [
        {"content": "低赞", "likes": 5},
        {"content": "高赞", "likes": 100},
        {"content": "中赞", "likes": 50},
    ]
    out = normalize_comments(raw)
    assert [c["likes"] for c in out] == [100, 50, 5]


def test_normalize_limit_10():
    raw = [{"content": f"c{i}", "likes": 100 - i} for i in range(20)]
    out = normalize_comments(raw)
    assert len(out) == 10


def test_normalize_handles_chinese_number():
    raw = [{"content": "x", "likes": "1.5万"}]
    out = normalize_comments(raw)
    assert out[0]["likes"] == 15000


def test_normalize_drops_empty_content():
    raw = [
        {"content": "", "likes": 100},
        {"content": "good", "likes": 50},
    ]
    out = normalize_comments(raw)
    assert len(out) == 1
    assert out[0]["text"] == "good"


def test_normalize_handles_none():
    assert normalize_comments(None) == []
    assert normalize_comments([]) == []


def test_adapt_profile_complete_with_collects():
    """v0.2.0 升级后输出含 collects/comments 字段."""
    user_info = {
        "nickname": "Ali Abdaal", "redId": "7947293444",
        "fans": "26.1万", "total_likes": "124万", "follows": "9",
    }
    raw_notes = [{
        "title": "AI 工作流", "type": "video",
        "likes": "1", "xsecToken": "T1", "noteId": "abc",
        "collects": "4295", "comments": "70", "cornerTag": "5月前",
    }]
    out = adapt_profile_complete(user_info, raw_notes,
                                  profile_url="https://x.com/u/Y?xsec_token=Z")
    assert out["blogger"]["fans"] == 261000
    assert out["blogger"]["total_likes"] == 1240000
    assert out["notes"][0]["collects"] == 4295
    assert out["notes"][0]["comments"] == 70
    assert out["notes"][0]["format"] == "视频"
    assert out["notes"][0]["cornerTag"] == "5月前"


def test_adapt_profile_handles_missing_numeric_fields():
    """字段缺失时标 None，不编造默认值."""
    user_info = {"nickname": "x"}  # 没有 fans
    raw_notes = [{"title": "y", "noteId": "z", "type": "normal"}]
    out = adapt_profile_complete(user_info, raw_notes)
    assert out["blogger"]["fans"] is None
    assert out["notes"][0]["collects"] is None
