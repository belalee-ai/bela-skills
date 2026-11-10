# S1 · 触发流程 · 四场景对话脚本

> 本文档是 SKILL.md 触发后 Claude 必须查阅的 **flow 手册**。
> 所有 ⭐ 标记 = 必须 ASK 用户的节点（守 C1 宪法「不擅自动手」）。

---

## 入口判别（必跑）

任意小红书链接出现 → 自动触发 `bela-xhs-analysis` → 跑入口逻辑：

1. **解析链接** → 短链 / 单篇笔记 / 博主主页 / 不能识别（终止）
2. **读 `user-config.json`**：
   - 不存在 → 走「首次配置」sub-flow（见末尾）
   - 存在 → 继续
3. **查 `{storage_root}/*/*-{博主名}*/_meta.json`** 是否存在
   - 存在 → 老博主（场景 2）
   - 不存在 → 新博主（场景 1 / 3 / 4）

---

## 场景 1 · 新博主 · 单篇笔记链接（最常见）

```
USER  → [甩链接] https://xiaohongshu.com/discovery/item/...?xsec_token=...

SKILL → 🔍 识别中：单篇笔记链接 · 博主"姜饼探AI"
        库内检查：⛔ 未入库 · 这是新博主

        我先抓这篇看下内容，约 30 秒 →

        [调 scripts/xhs_scraper.py 抓单篇 + scraper_adapter.adapt_single_note]

SKILL → ✅ 抓完了：
        ┌─────────────────────────────┐
        │ 标题：普通人学AI必看…         │
        │ 形式：图文 14 张              │
        │ 点赞 13 / 收藏 2644 / 评论 23 │
        │ 收藏点赞比 1:200 → 工具向干货 │
        └─────────────────────────────┘

⭐ ASK → 这个博主"姜饼探AI"要加入对标库吗？
        A) 是 · 走完整对标流程（再抓 2-3 分钟，建档案）
        B) 否 · 只这一篇 · 出单篇拆解报告就完事
        C) 让我先看更多再决定（先去博主主页瞄一眼）

USER  → A

⭐ ASK → 落盘到哪里？
        A) ~/Documents/xhs-竞品分析/  ⭐推荐（user-config 默认）
        B) iCloud Drive（同步到所有设备）
        C) 自定义路径（你输入）

USER  → A

⭐ ASK → 行业分类，归到哪一类？
        从你已有的目录看到：[AI工具] [营养师]
        A) AI工具
        B) 营养师
        C) 新建一类（你输入）

USER  → A

SKILL → 开始标准扫描（半年浅抓 + top5 深抓 + 你发的这篇）...
        [调 scripts/xhs_scraper.py 抓 profile + adapt_profile_notes]
        [对每篇 fresh note 调 utils.is_explosive(...) 算 is_explosive]
        [按 likes 降序取 top5 + 用户发的那篇，调 fetch_single_note]
        [实时回报 "已抓 38 篇浅扫，开始深抓爆文 1/5..."]

⭐ ASK → 深抓 5 篇爆文里，要不要顺手把口播版/图文版也抓出来？
        （视频笔记的 ASR 字幕会慢 ~30 秒/篇）
        A) 都要（多花 ~3 分钟）
        B) 只口播
        C) 只图文
        D) 都不要

USER  → C

SKILL → [对图文笔记调 scripts/media/ocr_images.sh]
        [classify_comments.build_dual_track(...) 处理评论]
        [render_readme.render(meta) 渲染 README]
        [写盘 _meta.json + README.md + notes/*.md + images/]

SKILL → ✅ 入库完成
        ┌────────────────────────────────────┐
        │ 路径：~/Documents/xhs-竞品分析/AI工具/小红书-姜饼探AI/
        │ 浅扫 38 篇 · 深抓 6 篇 · 图卡本地化 142 张
        │ 爆文 4 篇 · 半年外归档 0 篇
        │ 评论 top3 类已归纳（带原文证据）
        └────────────────────────────────────┘

        想看哪一份？
        A) 总览 README.md
        B) 你最初发的那篇深度拆解
        C) 进入 S5 流程 · 生成符合你风格的同主题口播
        D) 都不用，自己去文件夹翻
```

---

## 场景 2 · 老博主 · 又发链接（增量触发）

```
USER  → [甩链接]

SKILL → 🔍 识别：单篇笔记 · 博主"姜饼探AI"
        库内检查：✅ 已入库 · 上次扫描 2025-11-15（5 天前）

        [调 scripts/xhs_scraper.py 抓 profile fresh]
        [调 incremental_scan.compute_diff(meta, fresh, ...)]

SKILL → 📊 上次扫描以来的变化：
        ┌──────────────────────────────────┐
        │ 新发布笔记：3 篇                  │
        │ 数据涨幅 ≥30% 的老笔记：2 篇      │
        │ 你发的这篇是否在库：❌ 新内容      │
        │ 新爆文：1 篇（你发的这篇 2644 收藏） │
        └──────────────────────────────────┘

⭐ ASK → 怎么处理？
        A) 全部跑增量更新（标准 · 推荐）
        B) 只抓你发的这篇 + 新爆文
        C) 只看你发的这篇 · 不更新库
        D) 让我先看摘要再决定

USER  → A
        [对 new + major_change + new_explosive 调 fetch_single_note 深抓]
        [更新 _meta.json + 重渲染 README + append scan_history]
        [archive_old.archive_in_meta(...) 归档半年外]
```

---

## 场景 3 · 短链 / 主页链接

### 短链 `xhslink.com/...`

```
USER  → http://xhslink.com/o/57SsWjFSp7y
SKILL → 🔍 短链跳转 → 实际链接 [discovery/item/...]
        → 归入场景 1
```

### 主页 `xiaohongshu.com/user/profile/...`

```
USER  → 主页链接

SKILL → 🔍 识别：博主主页 · "姜饼探AI"

⭐ ASK → 没看到具体笔记，意图是？
        A) 直接对标入库（跳过单篇预览，直接走 profile 标准扫描）
        B) 先看博主前 12 篇是什么风格，再决定
        C) 取消
```

---

## 场景 4 · 不入库的临时分析

```
USER  → [甩链接]
SKILL → [抓单篇 + 摘要]
⭐ ASK → 加入对标库吗？
USER  → 否

SKILL → 好 · 只出单篇拆解报告。
        ┌─────────────────────────┐
        │ 报告内容：               │
        │ · 标题钩子套路           │
        │ · 视觉风格               │
        │ · 评论 top10 原文+归类   │
        │ · 可复用要素              │
        └─────────────────────────┘

⭐ ASK → 这份报告要存到哪？
        A) 临时输出（这次对话用完就丢）
        B) 存到默认临时区：{storage_root}/_临时单篇/
        C) 自定义路径
```

---

## 边界情况处理（必须实现）

| 情况 | skill 行为 | 实现位置 |
|---|---|---|
| 评论关闭 | `_meta.json.notes_index[].comments_disabled=true`；README 显示「评论已关」；**不强行编 top3 类** | `classify_comments.build_dual_track(None)` |
| 视频无字幕 | ⭐ ASK「跑 ASR？/ 跳过用标题概括」 | flow 编排层 |
| 链接失效 | `notes_index[].status="deleted"`，保留快照，不再尝试重抓 | `meta_store.upsert_note` |
| 网络/反爬中断 | 已抓部分先落盘；⭐ ASK「完成 X/Y，继续 / 暂停 / 降速重试」 | flow 编排层 |
| 同名博主歧义 | redId 唯一键，名字撞用 `小红书-{name}-{redId}/` | `paths.blogger_dir(..., redId=...)` |
| 爆文阈值动态 | 每次扫描重算粉丝量 → 重算 threshold → 写 `_meta.explosive_threshold` | `init_blogger.compute_threshold` |
| 用户原话保护 | 评论 top 10 写入 `notes/{slug}.md` 的「评论 top 10（原文 · 锁定不修改）」段；永不被 AI 改写 | `classify_comments` + single-note-template |

---

## 首次配置 sub-flow

skill 首次运行（未发现 `user-config.json`）：

```
SKILL → 👋 看起来你是第一次用我做对标博主追踪。
        我需要确认 2 个根目录，其他用安全默认值。

⭐ ASK → 对标库根目录放哪？
        A) ~/Documents/xhs-竞品分析  ⭐推荐
        B) iCloud Drive
        C) 自定义

⭐ ASK → 你的个人档案目录在哪？（S5 人设感知用）
        A) ~/Documents/个人档案
        B) ~/Magic AI-小周小李AI魔法规划相关/大力个人档案
        C) 自定义
        D) 暂时跳过（之后再设）

SKILL → ✅ 已生成 ~/.claude/skills/bela-xhs-analysis/user-config.json
        其他字段（爆文阈值 1000/5000、半年归档、ask 节点）用默认值。
        想改默认值，编辑 user-config.json 即可（参考 user-config.json.example）。
```
