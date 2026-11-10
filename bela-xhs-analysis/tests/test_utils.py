"""Tests for scripts/library/utils.py."""
import pytest
from scripts.library.utils import (
    slug_from_title,
    parse_chinese_number,
    is_explosive,
    iso_now,
)


class TestSlug:
    def test_basic_chinese(self):
        s = slug_from_title("普通人学AI必看，GitHub三步上手")
        # 12 个有效字符（逗号、空格被滤掉）
        assert len(s) <= 12
        assert "AI" in s
        assert "GitHub" in s or "Git" in s

    def test_strips_emoji(self):
        s = slug_from_title("🍪 GitHub 三步上手")
        assert "🍪" not in s
        assert " " not in s

    def test_strips_hashtag(self):
        s = slug_from_title("教程 #人工智能")
        assert "#" not in s
        assert " " not in s

    def test_max_len(self):
        assert len(slug_from_title("a" * 50)) == 12
        assert len(slug_from_title("a" * 50, max_len=5)) == 5


class TestParseChineseNumber:
    def test_plain(self):
        assert parse_chinese_number("3352") == 3352

    def test_wan(self):
        assert parse_chinese_number("3.1万") == 31000
        assert parse_chinese_number("1.5万") == 15000

    def test_w_lowercase(self):
        assert parse_chinese_number("11.2w") == 112000

    def test_zero(self):
        assert parse_chinese_number("0") == 0

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_chinese_number("abc")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_chinese_number("")


class TestIsExplosive:
    def test_low_fans_at_threshold(self):
        # 粉丝 1500 < 2000 → 阈值 1000；1000 赞 = 临界爆文
        assert is_explosive(likes=1000, fans=1500, fans_threshold=2000,
                            low=1000, high=5000) is True

    def test_low_fans_below(self):
        assert is_explosive(likes=999, fans=1500, fans_threshold=2000,
                            low=1000, high=5000) is False

    def test_high_fans_at_threshold(self):
        assert is_explosive(likes=5000, fans=15000, fans_threshold=2000,
                            low=1000, high=5000) is True

    def test_high_fans_below(self):
        assert is_explosive(likes=4999, fans=15000, fans_threshold=2000,
                            low=1000, high=5000) is False


class TestIsoNow:
    def test_format(self):
        s = iso_now()
        # 形如 2026-05-28T14:30:00+08:00
        assert "T" in s
        assert "+08:00" in s
