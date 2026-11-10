"""Tests for classify_comments.py (C2 宪法守门员)."""
from scripts.library.classify_comments import (
    can_classify, build_dual_track,
)


def test_can_classify_with_enough_comments():
    comments = [{"text": f"c{i}", "likes": 1} for i in range(10)]
    assert can_classify(comments) is True


def test_cannot_classify_with_few_comments():
    comments = [{"text": f"c{i}", "likes": 1} for i in range(5)]
    assert can_classify(comments) is False


def test_can_classify_returns_false_for_disabled():
    assert can_classify(None) is False
    assert can_classify([]) is False


def test_dual_track_too_few_preserves_original():
    comments = [
        {"text": "求教程", "likes": 32},
        {"text": "码住", "likes": 28},
    ]
    out = build_dual_track(comments)
    assert out["status"] == "too_few"
    assert "未做归类" in out["readme_block"]
    assert out["raw_top10"] == comments


def test_dual_track_disabled_comments():
    out = build_dual_track(None)
    assert out["status"] == "disabled"
    assert "评论已关" in out["readme_block"]
    assert out["raw_top10"] == []


def test_dual_track_each_class_has_evidence():
    """C2: 每类必须挂 ≥ 2 条原文."""
    comments = [{"text": f"评论{i}", "likes": 100 - i} for i in range(20)]
    classified = {
        "求教程类": ["评论0", "评论3"],
        "焦虑共鸣类": ["评论1", "评论4"],
        "求推荐类": ["评论2", "评论5"],
    }
    out = build_dual_track(comments, classified=classified)
    assert out["status"] == "classified"
    for klass, evidence in out["classes"].items():
        assert len(evidence) >= 2, f"{klass} 缺证据"


def test_dual_track_rejects_class_without_evidence():
    """AI 归类时某类挂不到 2 条原文 → 丢弃该类."""
    comments = [{"text": f"评论{i}", "likes": 100 - i} for i in range(10)]
    classified = {
        "类A": ["评论0", "评论1"],
        "类B": ["不存在的评论1", "不存在的评论2"],
    }
    out = build_dual_track(comments, classified=classified)
    assert "类A" in out["classes"]
    assert "类B" not in out["classes"]


def test_dual_track_all_classes_invalid_returns_no_classification():
    comments = [{"text": f"评论{i}", "likes": 100} for i in range(10)]
    classified = {"类X": ["不存在1", "不存在2"]}
    out = build_dual_track(comments, classified=classified)
    assert out["status"] == "no_classification"
    assert "未做归类" in out["readme_block"]
