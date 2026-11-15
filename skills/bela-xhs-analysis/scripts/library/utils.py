"""Pure utility functions for S1.

设计宪法 C2: 不幻觉. 所有解析失败时 raise，不返回猜测值.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone, timedelta


# 中文字符 / 字母 / 数字 / 中划线 / 下划线
_SLUG_VALID = re.compile(r"[一-鿿A-Za-z0-9\-_]")


def slug_from_title(title: str, max_len: int = 12) -> str:
    """从标题生成笔记 slug。

    规则：
    1. 取标题前 max_len 个有效字符（汉字/字母/数字/中划线/下划线）
    2. 去除空格、标点、emoji、# 话题符号
    """
    chars = [c for c in title if _SLUG_VALID.match(c)]
    return "".join(chars[:max_len])


def parse_chinese_number(s: str) -> int:
    """解析小红书返回的中文数字字符串。

    支持 "3352", "3.1万", "1.5w", "11.2w" 等格式。

    Raises:
        ValueError: 无法解析时抛错（守 C2 宪法）
    """
    s = s.strip()
    if not s:
        raise ValueError(f"empty string: {s!r}")

    # 去掉 trailing "+"（小红书 "1万+" "5000+" 这种约数）
    has_plus = s.endswith("+")
    if has_plus:
        s = s[:-1].strip()

    # 万 / w 后缀
    if s.endswith(("万", "w", "W")):
        prefix = s[:-1]
        try:
            return int(float(prefix) * 10000)
        except (ValueError, TypeError):
            raise ValueError(f"cannot parse 万/w number: {s!r}")

    try:
        return int(s)
    except (ValueError, TypeError):
        raise ValueError(f"cannot parse number: {s!r}")


def is_explosive(
    *,
    likes: int,
    fans: int,
    fans_threshold: int,
    low: int,
    high: int,
) -> bool:
    """判定笔记是否爆文。

    粉丝 < fans_threshold → 点赞 ≥ low 为爆文
    粉丝 ≥ fans_threshold → 点赞 ≥ high 为爆文
    """
    threshold = low if fans < fans_threshold else high
    return likes >= threshold


def iso_now() -> str:
    """当前时间 ISO 8601 字符串，带北京时区。"""
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")
