"""README.md 自动渲染.

设计宪法 C3: 有迹可循 - 链接保留 xsec_token；图片用相对路径.
设计宪法 C4: 真诚落地 - AI 归纳段必须标"AI 整理 · 可被你否决".
"""
from __future__ import annotations
from collections import Counter


def render(meta: dict) -> str:
    """从 _meta.json 渲染成完整 README.md 字符串."""
    blogger = meta["blogger"]
    threshold = meta["explosive_threshold"]
    active_notes = [n for n in meta.get("notes_index", [])
                    if n.get("status") == "active"]

    parts = [
        _header(meta, blogger),
        _profile(blogger, threshold),
        _format_distribution(active_notes),
        _topics_distribution_placeholder(),
        _notes_table(active_notes),
        _explosive_list(active_notes, threshold),
        _comments_top3_placeholder(),
        _diff_placeholder(),
    ]
    return "\n\n".join(p for p in parts if p)


def _header(meta: dict, blogger: dict) -> str:
    last_scan = "未扫描"
    if meta.get("scan_history"):
        last_scan = meta["scan_history"][-1]["date"]
    return (
        f"# 小红书 · {blogger['name']} · 竞品档案\n"
        f"> 行业：{blogger['industry']} · 平台：小红书 · "
        f"是否对标：{'✅' if blogger.get('is_target') else '❌'}\n"
        f"> 最后扫描：{last_scan}"
    )


def _profile(blogger: dict, threshold: int) -> str:
    fans = "?"
    if blogger.get("fans_count_history"):
        fans = blogger["fans_count_history"][-1]["count"]
    return (
        "## 博主画像\n"
        f"- **粉丝量**：{fans}（爆文阈值 = {threshold} 赞）\n"
        f"- **小红书号**：{blogger.get('redId', '?')}\n"
        f"- **userId**：{blogger.get('userId', '?')}\n"
        f"- **首次入库**：{blogger.get('first_seen', '?')}\n"
        f"- **数据可信度**：✅ 全部来自实际抓取，无 AI 推测"
    )


def _format_distribution(notes: list[dict]) -> str:
    if not notes:
        return ""
    counts = Counter(n["format"] for n in notes if "format" in n)
    if not counts:
        return ""
    total = sum(counts.values())
    lines = ["## 内容形式分布（自动统计）",
             "| 形式 | 数量 | 占比 |", "|---|---|---|"]
    for fmt, cnt in counts.most_common():
        pct = round(cnt * 100 / total)
        lines.append(f"| {fmt} | {cnt} | {pct}% |")
    return "\n".join(lines)


def _topics_distribution_placeholder() -> str:
    return (
        "## 选题主题分布（AI 整理 · 可被你否决）\n"
        "> 待 AI 主题归纳模块完成后自动填充"
    )


def _notes_table(notes: list[dict]) -> str:
    if not notes:
        return "## 笔记总览表\n\n暂无笔记."
    sorted_notes = sorted(notes, key=lambda n: n.get("date") or "", reverse=True)
    lines = [
        "## 笔记总览表（10 列 · 按时间倒序 · 半年内）",
        "| 日期 | 封面 | 标题 | 链接 | 形式 | 点赞 | 收藏 | 评论 | 是否爆文 | 详情 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for n in sorted_notes:
        cover = f"![](images/covers/{n['slug']}.webp)" if n.get("slug") else ""
        explosive = "✅" if n.get("is_explosive") else "❌"
        date_str = n.get("date") or ""
        date_short = date_str[5:] if date_str and len(date_str) >= 10 else (n.get("cornerTag") or "?")
        lines.append(
            f"| {date_short} | {cover} | {n.get('title','')} | "
            f"[→]({n.get('url','')}) | {n.get('format','?')} | "
            f"{n.get('likes',0)} | {n.get('collects',0)} | "
            f"{n.get('comments',0)} | {explosive} | "
            f"[详情]({n.get('file','')}) |"
        )
    return "\n".join(lines)


def _explosive_list(notes: list[dict], threshold: int) -> str:
    explosive = [n for n in notes if n.get("is_explosive")]
    if not explosive:
        return f"## 爆文榜（阈值 = {threshold} 赞）\n\n暂无爆文."
    sorted_e = sorted(explosive, key=lambda n: n.get("likes", 0), reverse=True)
    lines = [f"## 爆文榜（阈值 = {threshold} 赞）"]
    for n in sorted_e:
        lines.append(f"- {n.get('title','?')} — {n.get('likes',0)} 赞 "
                     f"[→]({n.get('file','')})")
    return "\n".join(lines)


def _comments_top3_placeholder() -> str:
    return (
        "## 评论区高频诉求 TOP 3（双轨 · 挂原文证据）\n"
        "> 待评论归类模块完成后自动填充（合并爆文样本）"
    )


def _diff_placeholder() -> str:
    return (
        "## 你和这个博主的差异化空间\n"
        "> 此段在 S5 人设感知生产模块完成后填充"
    )
