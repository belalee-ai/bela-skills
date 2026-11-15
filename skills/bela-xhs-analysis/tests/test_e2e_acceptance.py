"""端到端验收 · spec 9.1 的 T1-T8 用例（mock 网络层）.

测编排逻辑闭环：
- T1 新博主入库
- T2 增量场景
- T6 评论关闭兜底
- T8 半年归档
"""
from datetime import date
from scripts.library.init_blogger import build_meta, init_blogger_dirs
from scripts.library.incremental_scan import compute_diff
from scripts.library.archive_old import archive_in_meta
from scripts.library.classify_comments import build_dual_track
from scripts.library.render_readme import render
from scripts.library.meta_store import write_meta, read_meta, upsert_note


def test_T1_new_blogger_full_lifecycle(tmp_blogger_dir):
    """T1: 新博主单篇 → 建目录 + meta + 入库一篇笔记."""
    init_blogger_dirs(tmp_blogger_dir)
    assert (tmp_blogger_dir / "notes" / "_archive").is_dir()
    assert (tmp_blogger_dir / "images" / "covers").is_dir()

    meta = build_meta(
        {"name": "姜饼探AI", "redId": "X", "userId": "Y",
         "fans": 15000, "profile_url": "https://xhs.com/u/Y?xsec_token=A"},
        industry="AI工具", is_target=True,
        threshold=5000, today=date(2026, 5, 28),
    )
    upsert_note(meta, {
        "file": "notes/2025-11-15-github三步.md",
        "slug": "github三步", "date": "2025-11-15",
        "title": "GitHub 三步上手",
        "url": "https://xhs.com/discovery/item/X?xsec_token=A",
        "likes": 13, "collects": 2644, "comments": 23,
        "format": "图文", "is_explosive": True,
        "deep_scraped": True, "status": "active",
    })
    meta_file = tmp_blogger_dir / "_meta.json"
    write_meta(meta_file, meta)
    loaded = read_meta(meta_file)

    # C3: 有迹可循 - URL 保留 xsec_token
    assert "xsec_token=A" in loaded["notes_index"][0]["url"]
    # C3: 有迹可循 - blogger profile_url 保留
    assert "xsec_token=A" in loaded["blogger"]["profile_url"]
    # 结构完整
    assert loaded["schema_version"] == "1.0"
    assert loaded["blogger"]["is_target"] is True
    assert loaded["explosive_threshold"] == 5000


def test_T2_incremental_diff_summary(sample_meta):
    """T2: 同链接再发一次 → 增量算 diff."""
    sample_meta["notes_index"] = [
        {"slug": "a", "likes": 100, "collects": 100,
         "is_explosive": False, "status": "active"}
    ]
    fresh = [
        {"slug": "a", "likes": 105, "collects": 102},
        {"slug": "b", "likes": 1000, "collects": 500},
    ]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                       explosive_threshold=5000)
    assert "b" in diff["new"]
    assert "a" in diff["unchanged_or_minor"]


def test_T6_comments_disabled_no_classification():
    """T6: 评论关闭 → 不编 top3 类."""
    out = build_dual_track(None)
    assert out["status"] == "disabled"
    assert out["classes"] == {}
    assert "评论已关" in out["readme_block"]


def test_T8_old_notes_archived(sample_meta):
    """T8: 半年外笔记自动归档（不删，进 _archive/）."""
    sample_meta["notes_index"] = [
        {"slug": "fresh", "date": "2026-04-01",
         "file": "notes/fresh.md", "status": "active"},
        {"slug": "old", "date": "2024-12-01",
         "file": "notes/old.md", "status": "active"},
    ]
    archived = archive_in_meta(
        sample_meta, today=date(2026, 5, 28), after_days=180)
    assert len(archived) == 1
    assert archived[0]["slug"] == "old"
    assert archived[0]["file"] == "notes/_archive/old.md"
    assert archived[0]["status"] == "archived"
    # render 时归档的不出现在主表
    md = render(sample_meta)
    assert "fresh" in md  # active 还在
    assert "暂无笔记" not in md


def test_C2_constitution_evidence_required():
    """C2 宪法：归类必挂证据，否则丢弃."""
    comments = [{"text": f"c{i}", "likes": 50 - i} for i in range(15)]
    classified_with_fake = {
        "类A": ["c0", "c1"],
        "类B": ["不存在 1", "不存在 2"],  # 应被剔除
    }
    out = build_dual_track(comments, classified=classified_with_fake)
    assert "类A" in out["classes"]
    assert "类B" not in out["classes"]


def test_C3_constitution_url_preserves_token():
    """C3 宪法：URL 必须保留 xsec_token."""
    meta = build_meta(
        {"name": "x", "fans": 1000,
         "profile_url": "https://xhs.com/u/abc?xsec_token=TOKEN&app=pc"},
        industry="AI", is_target=True,
        threshold=1000, today=date(2026, 5, 28),
    )
    assert "xsec_token=TOKEN" in meta["blogger"]["profile_url"]
