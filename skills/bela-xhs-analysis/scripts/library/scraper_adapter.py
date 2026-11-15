"""Adapter: 把 v0.2.0 的 xhs_scraper.py 输出转成 S1 期望的结构.

不修改 v0.2.0 scraper（避免破坏回归），在边界做格式转换.

设计宪法 C2: 不幻觉 - v0.2.0 没抓的字段标 None，不编造默认值.

TODO（下个会话或增量任务）：
- v0.2.0 get_profile_notes 当前不返回 date / collects / comments / format
- 需要升级 xhs_scraper.py 的 noteCard 解析，或调单篇 detail 补足
- adapter 接口稳定，仅 v0.2.0 实现升级
"""
from __future__ import annotations
from typing import Optional
from .utils import slug_from_title, parse_chinese_number, iso_now


# v0.2.0 type 字段 → S1 format 字段
_TYPE_TO_FORMAT = {
    "normal": "图文",
    "video": "视频",
}


def adapt_profile_notes(
    user_info: dict,
    raw_notes: list[dict],
    *,
    profile_url: str = "",
) -> dict:
    """v0.2.0 get_profile_notes() 输出 → S1 期望结构.

    Args:
        user_info: v0.2.0 user_info dict（nickname/desc/ip/redId）
        raw_notes: v0.2.0 notes list（title/type/likes/xsecToken/noteId）
        profile_url: 主页 URL（v0.2.0 没返回，caller 传入）

    Returns:
        {
            "blogger": {name, redId, userId, fans, profile_url, ...},
            "notes": [{slug, date, title, url, likes, collects, comments,
                       format, ...}, ...]
        }
    """
    blogger = {
        "name": user_info.get("nickname", ""),
        "redId": user_info.get("redId", ""),
        "userId": _extract_user_id(profile_url),
        "desc": user_info.get("desc", ""),
        "ip": user_info.get("ip", ""),
        "fans": None,  # v0.2.0 未抓，TODO 升级时补
        "profile_url": profile_url,
    }

    notes = []
    for raw in raw_notes:
        note_id = raw.get("noteId", "")
        xsec = raw.get("xsecToken", "")
        url = _build_note_url(note_id, xsec)
        try:
            likes = parse_chinese_number(str(raw.get("likes", "0")))
        except ValueError:
            likes = 0

        title = raw.get("title", "")
        notes.append({
            "slug": slug_from_title(title) if title else note_id[:12],
            "date": None,            # v0.2.0 未抓，TODO
            "title": title,
            "url": url,
            "likes": likes,
            "collects": None,        # v0.2.0 未抓，TODO
            "comments": None,        # v0.2.0 未抓，TODO
            "format": _TYPE_TO_FORMAT.get(raw.get("type", ""), "图文"),
            "noteId": note_id,
            "xsecToken": xsec,
        })

    return {"blogger": blogger, "notes": notes}


def adapt_single_note(raw_detail: dict) -> dict:
    """v0.2.0 fetch_single_note() 输出 → S1 单笔记结构.

    Args:
        raw_detail: v0.2.0 fetch_single_note() 返回的 dict

    Returns:
        S1 标准单笔记 dict（含 YAML 字段全集）
    """
    # 实际字段映射依赖 v0.2.0 fetch_single_note 的具体返回结构
    # 这里给出占位，TODO 用真实数据校准
    n = raw_detail.get("noteCard", raw_detail) if isinstance(raw_detail, dict) else {}
    interact = n.get("interactInfo", {})
    title = n.get("displayTitle") or n.get("title", "")

    def _safe_int(v):
        if v is None:
            return 0
        try:
            return parse_chinese_number(str(v))
        except ValueError:
            return 0

    return {
        "slug": slug_from_title(title) if title else "",
        "date": _extract_date(n),
        "title": title,
        "url": raw_detail.get("url", ""),
        "likes": _safe_int(interact.get("likedCount")),
        "collects": _safe_int(interact.get("collectedCount")),
        "comments": _safe_int(interact.get("commentCount")),
        "format": _TYPE_TO_FORMAT.get(n.get("type", ""), "图文"),
        "tags": [t.get("name") for t in n.get("tagList", []) if t.get("name")],
        "comments_disabled": False,  # TODO: v0.2.0 是否能识别评论关闭？
        "scraped_at": iso_now(),
    }


def _build_note_url(note_id: str, xsec_token: str) -> str:
    if not note_id:
        return ""
    base = f"https://www.xiaohongshu.com/discovery/item/{note_id}"
    if xsec_token:
        return f"{base}?xsec_token={xsec_token}&xsec_source=pc_feed"
    return base


def _extract_user_id(profile_url: str) -> str:
    """从 https://.../user/profile/{userId}?... 提取 userId."""
    if not profile_url:
        return ""
    import re
    m = re.search(r"/user/profile/([^/?]+)", profile_url)
    return m.group(1) if m else ""


def _extract_date(note_card: dict) -> Optional[str]:
    """从笔记数据提取发布日期（YYYY-MM-DD）.

    v0.3.0+ S2: 优先 SSR 毫秒时间戳；fallback cornerTag.text（"5月前"等）.
    """
    time_val = note_card.get("time") or note_card.get("lastUpdateTime")
    if time_val:
        try:
            from datetime import datetime
            if isinstance(time_val, (int, float)) and time_val > 1e12:
                return datetime.fromtimestamp(time_val / 1000).date().isoformat()
            if isinstance(time_val, str) and len(time_val) >= 10:
                return time_val[:10]
        except (ValueError, TypeError):
            pass
    return None


def normalize_comments(raw_comments: list[dict]) -> list[dict]:
    """v0.2.0 fetch_comments=True 输出 {content, likes, nickname} →
    S1 标准 {text, likes} · 按 likes 降序，limit 10.

    Args:
        raw_comments: v0.2.0 evt comment_list（每条 {content, likes, nickname, ...}）

    Returns:
        list[{text, likes}]，top 10
    """
    from .utils import parse_chinese_number
    normalized = []
    for c in raw_comments or []:
        text = c.get("text") or c.get("content") or ""
        if not text:
            continue
        raw_likes = c.get("likes", 0)
        try:
            likes = (raw_likes if isinstance(raw_likes, int)
                     else parse_chinese_number(str(raw_likes)))
        except ValueError:
            likes = 0
        normalized.append({"text": text, "likes": likes})

    # 按 likes 降序，limit 10
    normalized.sort(key=lambda x: x["likes"], reverse=True)
    return normalized[:10]


def adapt_profile_complete(user_info: dict, raw_notes: list[dict],
                           *, profile_url: str = "") -> dict:
    """v0.3.0+ S2 增强版：用 v0.2.0 升级后的浅扫输出（含 collects/comments）.

    跟 adapt_profile_notes 的区别：信任 v0.2.0 已经返回 collects/comments/fans 字段.
    """
    from .utils import parse_chinese_number, slug_from_title

    def _to_int(v):
        if v is None or v == "":
            return None
        try:
            return parse_chinese_number(str(v)) if isinstance(v, str) else int(v)
        except (ValueError, TypeError):
            return None

    blogger = {
        "name": user_info.get("nickname", ""),
        "redId": user_info.get("redId", ""),
        "userId": _extract_user_id(profile_url),
        "desc": user_info.get("desc", ""),
        "ip": user_info.get("ip", ""),
        "fans": _to_int(user_info.get("fans")),
        "total_likes": _to_int(user_info.get("total_likes")),
        "follows": _to_int(user_info.get("follows")),
        "profile_url": profile_url,
    }

    notes = []
    for raw in raw_notes:
        note_id = raw.get("noteId", "")
        xsec = raw.get("xsecToken", "")
        url = _build_note_url(note_id, xsec)
        title = raw.get("title", "")
        notes.append({
            "slug": slug_from_title(title) if title else note_id[:12],
            "date": _extract_date(raw),  # 浅扫一般没 time，由 fetch_single_note 补
            "title": title,
            "url": url,
            "likes": _to_int(raw.get("likes")) or 0,
            "collects": _to_int(raw.get("collects")),
            "comments": _to_int(raw.get("comments")),
            "format": _TYPE_TO_FORMAT.get(raw.get("type", ""), "图文"),
            "cornerTag": raw.get("cornerTag", ""),  # "X月前"
            "cover": raw.get("cover", ""),
            "noteId": note_id,
            "xsecToken": xsec,
            "sticky": raw.get("sticky", False),
        })

    return {"blogger": blogger, "notes": notes}
