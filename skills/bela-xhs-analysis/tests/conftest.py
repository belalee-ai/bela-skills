"""Pytest fixtures for S1 tests."""
import sys
from pathlib import Path

# 让 tests 能 import scripts.library.*
_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

import pytest


@pytest.fixture
def sample_meta():
    """A canonical _meta.json sample matching schema v1.0."""
    return {
        "schema_version": "1.0",
        "blogger": {
            "platform": "xhs",
            "name": "姜饼探AI",
            "redId": "95475810861",
            "userId": "672bcca5000000001c01bfed",
            "industry": "AI工具",
            "is_target": True,
            "first_seen": "2026-05-28",
            "fans_count_history": [{"date": "2026-05-28", "count": 15000}],
            "profile_url": "https://www.xiaohongshu.com/user/profile/672bcca5000000001c01bfed?xsec_token=test",
        },
        "explosive_threshold": 5000,
        "scan_history": [],
        "notes_index": [],
    }


@pytest.fixture
def tmp_blogger_dir(tmp_path):
    """A tmp dir structured like a blogger folder."""
    bdir = tmp_path / "AI工具" / "小红书-姜饼探AI"
    (bdir / "notes" / "_archive").mkdir(parents=True)
    (bdir / "images" / "covers").mkdir(parents=True)
    (bdir / "images" / "slides").mkdir(parents=True)
    return bdir
