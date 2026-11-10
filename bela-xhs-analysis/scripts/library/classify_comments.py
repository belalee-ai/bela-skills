"""评论双轨归类（C2 宪法核心：底层固化原文 + AI 归类挂证据）.

设计宪法 C2: 不幻觉 - 每个归类必须挂 ≥ 2 条原文证据，否则丢弃该类.
"""
from __future__ import annotations
from typing import Optional


MIN_COMMENTS_TO_CLASSIFY = 10
MIN_EVIDENCE_PER_CLASS = 2


def can_classify(comments: Optional[list[dict]]) -> bool:
    if comments is None:
        return False
    return len(comments) >= MIN_COMMENTS_TO_CLASSIFY


def _render_too_few(comments: list[dict]) -> str:
    lines = ["## 评论 top {0}（评论较少，未做归类）".format(len(comments)), ""]
    for i, c in enumerate(comments, 1):
        lines.append(f'{i}. "{c["text"]}" · {c["likes"]}赞')
    return "\n".join(lines)


def _render_disabled() -> str:
    return "## 评论\n\n评论已关 · 未抓取."


def _render_classified(comments: list[dict],
                       classes: dict[str, list[str]]) -> str:
    lines = ["## 评论区高频诉求 TOP 3（合并爆文样本 · 每类挂原文证据）", ""]
    circled = "①②③④⑤⑥⑦⑧⑨⑩"
    for i, (klass, evidence_texts) in enumerate(classes.items(), 1):
        prefix = circled[i - 1] if i <= 10 else f"({i})"
        lines.append(f"### {prefix} {klass}（{len(evidence_texts)} 条）")
        for ev_text in evidence_texts:
            matched = next((c for c in comments if c["text"] == ev_text), None)
            likes = matched["likes"] if matched else "?"
            lines.append(f'- "{ev_text}" · {likes}赞')
        lines.append("")
    return "\n".join(lines)


def build_dual_track(
    comments: Optional[list[dict]],
    classified: Optional[dict[str, list[str]]] = None,
) -> dict:
    """构建双轨格式输出.

    Args:
        comments: top 10 评论原文 list[{text, likes}]，None=评论关闭
        classified: AI 归类 {类名: [评论原文 list]}

    Returns:
        {"status": "disabled"|"too_few"|"no_classification"|"classified",
         "raw_top10": list, "classes": dict, "readme_block": str}
    """
    if comments is None:
        return {
            "status": "disabled",
            "raw_top10": [],
            "classes": {},
            "readme_block": _render_disabled(),
        }

    if not can_classify(comments):
        return {
            "status": "too_few",
            "raw_top10": comments,
            "classes": {},
            "readme_block": _render_too_few(comments),
        }

    if not classified:
        return {
            "status": "no_classification",
            "raw_top10": comments,
            "classes": {},
            "readme_block": _render_too_few(comments),
        }

    # C2 守门：每类必须挂 ≥ 2 条真实原文
    available_texts = {c["text"] for c in comments}
    valid_classes: dict[str, list[str]] = {}
    for klass, evidence_texts in classified.items():
        valid_evidence = [t for t in evidence_texts if t in available_texts]
        if len(valid_evidence) >= MIN_EVIDENCE_PER_CLASS:
            valid_classes[klass] = valid_evidence

    if not valid_classes:
        return {
            "status": "no_classification",
            "raw_top10": comments,
            "classes": {},
            "readme_block": _render_too_few(comments),
        }

    return {
        "status": "classified",
        "raw_top10": comments,
        "classes": valid_classes,
        "readme_block": _render_classified(comments, valid_classes),
    }
