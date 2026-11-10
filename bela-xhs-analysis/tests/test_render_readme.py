"""Tests for render_readme.py."""
from scripts.library.render_readme import render


def test_render_includes_required_sections(sample_meta):
    sample_meta["notes_index"] = [
        {
            "slug": "github三步", "date": "2025-11-15",
            "title": "GitHub 三步上手", "url": "https://x?xsec_token=A",
            "likes": 13, "collects": 2644, "comments": 23,
            "format": "图文", "is_explosive": True,
            "file": "notes/2025-11-15-github三步.md",
            "status": "active",
        },
    ]
    md = render(sample_meta)
    assert "# 小红书 · 姜饼探AI · 竞品档案" in md
    assert "博主画像" in md
    assert "笔记总览表" in md
    assert "爆文榜" in md
    assert "github三步" in md
    assert "xsec_token=A" in md  # URL 保留 token
    assert "2644" in md


def test_render_excludes_archived(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "old", "date": "2024-01-01", "title": "老笔记",
         "url": "u", "likes": 5, "collects": 5, "comments": 1,
         "format": "图文", "is_explosive": False,
         "file": "notes/_archive/old.md", "status": "archived"},
    ]
    md = render(sample_meta)
    assert "老笔记" not in md


def test_render_handles_empty_notes(sample_meta):
    md = render(sample_meta)
    assert "暂无笔记" in md


def test_render_format_distribution(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "a", "date": "2025-11-15", "title": "A", "url": "u",
         "likes": 0, "collects": 0, "comments": 0, "format": "图文",
         "is_explosive": False, "file": "notes/a.md", "status": "active"},
        {"slug": "b", "date": "2025-11-14", "title": "B", "url": "u",
         "likes": 0, "collects": 0, "comments": 0, "format": "视频",
         "is_explosive": False, "file": "notes/b.md", "status": "active"},
    ]
    md = render(sample_meta)
    assert "图文" in md and "视频" in md


def test_render_is_target_flag(sample_meta):
    md = render(sample_meta)
    assert "是否对标：✅" in md


def test_render_explosive_list_sorts_by_likes(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "a", "date": "2025-11-15", "title": "A 普通", "url": "u",
         "likes": 6000, "collects": 0, "comments": 0, "format": "图文",
         "is_explosive": True, "file": "notes/a.md", "status": "active"},
        {"slug": "b", "date": "2025-11-14", "title": "B 高赞", "url": "u",
         "likes": 30000, "collects": 0, "comments": 0, "format": "图文",
         "is_explosive": True, "file": "notes/b.md", "status": "active"},
    ]
    md = render(sample_meta)
    # 在「爆文榜」段内排序：B 在前
    explosive_section = md.split("## 爆文榜")[1].split("##")[0]
    idx_a = explosive_section.index("A 普通")
    idx_b = explosive_section.index("B 高赞")
    assert idx_b < idx_a
