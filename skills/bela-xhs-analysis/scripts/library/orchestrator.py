"""S2 · Orchestrator：把 v0.2.0 scraper + S1 库模块串成完整链路.

用法：
    python3 -m scripts.library.orchestrator --url URL --industry "AI工具"

输入：单篇笔记链接 / 短链 / 博主主页链接
输出：~/Documents/xhs-竞品分析/{行业}/小红书-{博主名}/ 完整档案

设计宪法守护：
- C1 不擅自动手：CLI 必传 --industry，--no-asr 等开关
- C2 不幻觉：缺字段标 None，不编造
- C3 有迹可循：所有 URL 保留 xsec_token，时间戳带时区
- C5 数据兜底：先读 user-config，没有用默认值
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import date

# 让 import scripts.* 可用
_SKILL_ROOT = Path(__file__).resolve().parents[2]
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from scripts.library.paths import (
    load_user_config, blogger_dir, meta_path, readme_path,
    notes_dir, DEFAULT_CONFIG,
)
from scripts.library.init_blogger import (
    init_blogger_dirs, compute_threshold, build_meta,
)
from scripts.library.meta_store import (
    read_meta, write_meta, upsert_note, append_scan_history, find_note_by_url,
)
from scripts.library.scraper_adapter import (
    adapt_single_note, adapt_profile_complete, normalize_comments,
)
from scripts.library.classify_comments import build_dual_track
from scripts.library.render_readme import render
from scripts.library.archive_old import archive_in_meta
from scripts.library.utils import is_explosive, iso_now


def run_analysis(
    url: str,
    *,
    industry: str,
    cfg: dict | None = None,
    enable_asr: bool = False,
    deep_top_n: int = 5,
    today: date | None = None,
) -> dict:
    """端到端：用户给 URL → 出对标档案.

    Returns:
        {"blogger_dir": Path, "meta": dict, "scenario": "new"|"incremental"|"single"}
    """
    cfg = cfg or load_user_config()
    today = today or date.today()

    # === 1. 抓单篇（v0.2.0）===
    import scripts.xhs_scraper as scraper
    cookie = scraper.get_cookie()

    note_id = scraper.parse_note_id_from_url(url)
    xsec = scraper.parse_xsec_token_from_url(url)
    detail = scraper.get_note_detail(note_id, cookie, xsec, fetch_comments=True)

    if not detail:
        return {"error": f"无法抓取笔记: {url}"}

    # === 2. 找博主 profile_url，浅扫 profile ===
    # 单篇 URL 不含 author profile URL，需要从笔记 detail 里提取
    # 但 v0.2.0 detail 没返回 author。简化方案：跳过 profile 浅扫，只入这一篇.
    # （TODO 在下次迭代解决: 从 note SSR 数据提取 author.userId）

    # === 3. 组装 blogger_data（先从 detail 里 author 字段取，再去 profile 补全 fans）===
    author_userId = detail.get("author_userId", "")
    author_nickname = detail.get("author_nickname", "")
    author_xsec = detail.get("author_xsec_token", "")
    blogger_data = {
        "name": author_nickname,
        "redId": "",   # 主页扫描时补
        "userId": author_userId,
        "fans": None,  # 主页扫描时补
        "profile_url": "",
    }

    # 如果有 author_userId，去主页抓 fans + redId
    if author_userId:
        profile_url = f"https://www.xiaohongshu.com/user/profile/{author_userId}"
        if author_xsec:
            profile_url += f"?xsec_token={author_xsec}"
        try:
            user_info, _profile_notes_raw = scraper.get_profile_notes(profile_url)
            from scripts.library.utils import parse_chinese_number
            blogger_data["redId"] = user_info.get("redId", "")
            blogger_data["profile_url"] = profile_url
            fans_raw = user_info.get("fans", "")
            if fans_raw:
                try:
                    blogger_data["fans"] = parse_chinese_number(str(fans_raw))
                except ValueError:
                    pass
            if not blogger_data["name"]:
                blogger_data["name"] = user_info.get("nickname", "")
        except Exception as e:
            print(f"   ⚠️  主页扫描失败（继续单篇）: {e}", file=sys.stderr)

    if not blogger_data["name"]:
        return {"error": "未能从笔记抓到作者信息，请用博主主页 URL 重跑"}

    # === 4. 算爆文阈值（守 C2 宪法：fans 未知时用 high 严格兜底，不误报爆文）===
    fans_known = blogger_data["fans"] is not None
    fans = blogger_data["fans"] if fans_known else cfg["fans_threshold"]  # 未知时按"大账号"算
    threshold = compute_threshold(
        fans=fans,
        fans_threshold=cfg["fans_threshold"],
        low=cfg["explosive_threshold_low"],
        high=cfg["explosive_threshold_high"],
    )

    # === 5. 检查库 ===
    bdir = blogger_dir(cfg, industry=industry, platform="xhs",
                       name=blogger_data["name"])
    existing_meta_p = meta_path(bdir)
    scenario = "incremental" if existing_meta_p.exists() else "new"

    if scenario == "new":
        init_blogger_dirs(bdir)
        meta = build_meta(blogger_data, industry=industry, is_target=True,
                          threshold=threshold, today=today)
    else:
        meta = read_meta(existing_meta_p)

    # === 5.5 浅扫博主主页其他笔记（profile shallow scan）===
    if author_userId:
        try:
            from scripts.library.scraper_adapter import adapt_profile_complete
            user_info_full, raw_notes = scraper.get_profile_notes(profile_url)
            adapted = adapt_profile_complete(
                user_info_full, raw_notes, profile_url=profile_url,
            )
            for shallow_note in adapted["notes"]:
                # 不覆盖已深抓的笔记
                if any(n.get("slug") == shallow_note["slug"]
                       for n in meta.get("notes_index", [])):
                    continue
                # 算 is_explosive
                likes_v = shallow_note["likes"] or 0
                shallow_note["is_explosive"] = is_explosive(
                    likes=likes_v, fans=fans,
                    fans_threshold=cfg["fans_threshold"],
                    low=cfg["explosive_threshold_low"],
                    high=cfg["explosive_threshold_high"],
                )
                shallow_note["last_updated"] = iso_now()
                shallow_note["deep_scraped"] = False
                shallow_note["asr_extracted"] = False
                shallow_note["comments_disabled"] = False
                shallow_note["status"] = "active"
                shallow_note["file"] = f"notes/{shallow_note.get('date') or today.isoformat()}-{shallow_note['slug']}.md"
                shallow_note.pop("noteId", None)
                shallow_note.pop("xsecToken", None)
                shallow_note.pop("sticky", None)
                upsert_note(meta, shallow_note)
            print(f"   ✅ 浅扫入库 {len(adapted['notes'])} 篇笔记")
        except Exception as e:
            print(f"   ⚠️  profile 浅扫部分失败: {e}", file=sys.stderr)

    # === 6. 把这一篇深抓笔记 upsert 进去 ===
    likes = _safe_int(detail.get("likes")) or 0
    note_record = {
        "file": f"notes/{today.isoformat()}-{_safe_slug(detail.get('title',''))}.md",
        "slug": _safe_slug(detail.get("title", "")),
        "date": today.isoformat(),  # TODO: 用 SSR time 字段
        "title": detail.get("title", ""),
        "url": url,
        "likes": likes,
        "collects": _safe_int(detail.get("collects")),
        "comments": _safe_int(detail.get("comments")),
        "format": "视频" if detail.get("type") == "video" else "图文",
        "is_explosive": is_explosive(
            likes=likes, fans=fans, fans_threshold=cfg["fans_threshold"],
            low=cfg["explosive_threshold_low"],
            high=cfg["explosive_threshold_high"],
        ),
        "last_updated": iso_now(),
        "deep_scraped": True,
        "asr_extracted": False,  # 本次 orchestrator 不做 ASR（C 决策延后视频处理）
        "comments_disabled": detail.get("comments_disabled", False),
        "status": "active",
    }
    upsert_note(meta, note_record)

    # === 7. 写单笔记 .md（含 YAML + 评论 top10 + 归类）===
    raw_comments = detail.get("comment_list", [])
    top10 = normalize_comments(raw_comments)
    dual = build_dual_track(top10 if top10 else None)
    _write_note_md(bdir, note_record, detail, top10, dual)

    # === 8. 归档半年外 ===
    archive_in_meta(meta, today=today, after_days=cfg["archive_after_days"])

    # === 9. append scan history ===
    append_scan_history(meta, {
        "date": iso_now(),
        "notes_scanned": 1, "notes_deep": 1,
        "new_explosive": 1 if note_record["is_explosive"] else 0,
    })

    # === 9.5 · 下载用户提交那篇深抓的封面（best-effort，5s 超时） ===
    for n in meta.get("notes_index", []):
        if n.get("slug") == note_record["slug"] and n.get("cover"):
            ok = _download_cover(bdir, n["slug"], n["cover"], timeout=5)
            print(f"   {'✅' if ok else '⚠️'} 封面图下载 → images/covers/{n['slug']}")
            break

    # === 10. 落盘 ===
    write_meta(existing_meta_p, meta)
    readme_path(bdir).write_text(render(meta), encoding="utf-8")

    return {
        "blogger_dir": bdir,
        "meta": meta,
        "scenario": scenario,
        "note_slug": note_record["slug"],
    }


def _safe_int(v):
    if v is None or v == "":
        return None
    if isinstance(v, int):
        return v
    try:
        from scripts.library.utils import parse_chinese_number
        return parse_chinese_number(str(v))
    except ValueError:
        return None


def _safe_slug(title: str) -> str:
    from scripts.library.utils import slug_from_title
    return slug_from_title(title) if title else "untitled"


def _extract_author_from_detail(detail: dict) -> str:
    """v0.2.0 detail 没显式返回 author，需要 hacky 提取."""
    return detail.get("nickname", "") or detail.get("author", "")


def _download_cover(bdir: Path, slug: str, cover_url: str, timeout: int = 10) -> bool:
    """下载封面图到 images/covers/{slug}.{ext}.

    C3 有迹可循 - 图片本地化防 CDN 挂.
    Returns True 成功, False 失败（不抛错）.
    """
    import urllib.request, urllib.error
    if not cover_url or not cover_url.startswith("http"):
        return False
    try:
        # 推断扩展名
        ext = ".webp"
        if ".jpg" in cover_url.lower():
            ext = ".jpg"
        elif ".png" in cover_url.lower():
            ext = ".png"
        target = bdir / "images" / "covers" / f"{slug}{ext}"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return True  # 已存在
        req = urllib.request.Request(
            cover_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            target.write_bytes(r.read())
        return True
    except Exception:
        return False


def _write_note_md(bdir: Path, note_record: dict, raw_detail: dict,
                    top10: list[dict], dual: dict) -> None:
    """写单笔记 .md（含 YAML front matter + 正文 + 评论双轨）."""
    try:
        import yaml as _yaml_maybe
        yaml_dump = _yaml_maybe.safe_dump
    except (ImportError, ModuleNotFoundError, AttributeError):
        yaml_dump = None

    # YAML front matter
    yaml_fields = {
        k: v for k, v in note_record.items()
        if k in {"date", "slug", "title", "url", "likes", "collects",
                 "comments", "format", "is_explosive", "deep_scraped",
                 "asr_extracted", "comments_disabled"}
    }
    yaml_fields["scraped_at"] = note_record["last_updated"]
    yaml_fields["tags"] = raw_detail.get("tags", [])

    if yaml_dump:
        yaml_str = yaml_dump(yaml_fields, allow_unicode=True,
                              default_flow_style=False, sort_keys=False)
    else:
        # fallback：手写 YAML（不依赖 yaml 库）
        yaml_str = ""
        for k, v in yaml_fields.items():
            if isinstance(v, list):
                yaml_str += f"{k}: [{', '.join(str(x) for x in v)}]\n"
            elif isinstance(v, bool):
                yaml_str += f"{k}: {str(v).lower()}\n"
            else:
                yaml_str += f"{k}: {v}\n"

    md_parts = [
        "---",
        yaml_str.strip(),
        "---",
        "",
        f"## 封面",
        f"![](../images/covers/{note_record['slug']}.webp)",
        "",
        f"## 正文",
        "",
        raw_detail.get("desc", "（无 desc）").strip(),
        "",
        "## 评论 top 10（原文 · 锁定不修改）",
        "",
    ]
    if top10:
        for i, c in enumerate(top10, 1):
            md_parts.append(f'{i}. "{c["text"]}" · {c["likes"]}赞')
    else:
        md_parts.append("（无评论或评论已关）")

    md_parts.extend(["", dual["readme_block"]])

    file_path = bdir / note_record["file"]
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("\n".join(md_parts), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="S2 端到端竞品分析编排")
    parser.add_argument("--url", required=True, help="笔记链接（短链/单篇/主页）")
    parser.add_argument("--industry", required=True,
                        help="行业分类（如 AI工具/营养师）")
    parser.add_argument("--no-asr", action="store_true",
                        help="跳过视频 ASR（默认就关；显式选项保留以备未来）")
    args = parser.parse_args()

    result = run_analysis(args.url, industry=args.industry,
                          enable_asr=not args.no_asr)
    if "error" in result:
        print(f"❌ {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ {result['scenario']} 完成")
    print(f"   blogger_dir: {result['blogger_dir']}")
    print(f"   note_slug: {result['note_slug']}")
    print(f"   README: {result['blogger_dir'] / 'README.md'}")


if __name__ == "__main__":
    main()
