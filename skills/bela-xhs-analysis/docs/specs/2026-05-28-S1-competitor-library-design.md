# S1 · 对标博主库 · 设计文档

| 字段 | 值 |
|---|---|
| Spec ID | S1 |
| Skill | `bela-xhs-analysis` |
| 目标版本 | `v0.3.0` |
| 当前版本 | `v0.2.0` |
| 设计日期 | 2026-05-28 |
| 状态 | 设计完成 · 待用户 review |
| 上游 | v0.2.0 已有的"单次分析引擎"（`xhs_scraper.py` / `media/*.sh`） |
| 下游 | S2 正文/口播抓取 · S3 多格式产出 · S5 人设感知生产 · S4 跨设备路径 |

---

## 0 · 设计宪法（核心约束 · 不可违背）

| 编号 | 条款 | 落地动作 |
|---|---|---|
| C1 🚫 | **不擅自动手** | 关键节点必须 ask 用户；不预设默认到底 |
| C2 🚫 | **不幻觉** | 数据必须来自实际抓取或用户输入；AI 归纳必挂原文证据 |
| C3 ✅ | **有迹可循** | 每条数据标注来源（URL / 文件 / 用户原话），可反向追溯 |
| C4 ✅ | **真诚落地** | 不夸张、不堆华丽辞藻；语气符合用户人设（理工/克制/探索者） |
| C5 ♻️ | **数据兜底流程** | 先读本地 → 没有再问用户 → 用户提供后再跑 |

---

## 1 · 目标与非目标

### 1.1 目标

把 `bela-xhs-analysis` 从"单次分析工具"升级为"持续追踪的对标博主库"：

1. 用户发任意 xhs 链接 → skill 自动判断博主是否已入库
2. 新博主可一键建档（行业分类 / 浅+深抓 / 评论归类）
3. 老博主自动算增量差量（新发布 / 数据涨幅 / 半年归档）
4. 所有数据本地化（图片下载、原始 URL 保留），可跨设备同步
5. 落盘格式对下游 skill 友好（YAML + JSON 双重元数据）

### 1.2 非目标（本期不做）

- ❌ 跨平台支持（抖音 / B站 / 微博）—— 命名预留，实施延后
- ❌ S5 人设生产 —— 单独 spec
- ❌ S4 跨设备同步实施 —— 单独 spec（本期只做路径变量化预留口子）
- ❌ Web UI / GUI —— 纯 CLI / skill 对话模式
- ❌ 实时监控（定时巡检博主新内容）—— 暂走用户手动触发

---

## 2 · 五个核心设计决策（已 brainstorm 锁定）

| # | 决策点 | 选定方案 | 理由摘要 |
|---|---|---|---|
| D1 | 多平台扩展 | **B · 命名预留** | 命名含 `{平台}-` 字段，文件夹按行业分类；将来加平台 0 重构 |
| D2 | 存储形态 | **B · 博主文件夹** | README + notes/ + images/ + \_meta.json，结构清晰、图片本地化、可程序化读取 |
| D3 | 采集深度 | **B · 标准扫描** | 半年浅抓全部 + top5 深抓 + 用户指定那篇深抓；2-3 分钟完成 |
| D4 | 更新策略 | **B · 智能增量** | 对比 `_meta.json` 算差量；新内容 / 大涨幅 / 半年外归档 |
| D5 | 评论 top3 类 | **C · 双轨** | 底层 top 10 评论原文锁定 + AI 归类挂证据 |

---

## 3 · 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    bela-xhs-analysis (S1)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   用户发 xhs 链接                                            │
│        ↓                                                     │
│   ┌─────────────┐                                            │
│   │ 1. 链接识别  │  → 单篇 / 主页 / 短链                       │
│   └─────────────┘                                            │
│        ↓                                                     │
│   ┌─────────────┐                                            │
│   │ 2. 库内检查  │  → 查 {storage_root}/                       │
│   └─────────────┘                                            │
│        ├── 新博主 → "首次扫描"流程                            │
│        ├── 老博主 → "智能增量"流程                            │
│        └── 单次分析 → 跳过入库                                │
│        ↓                                                     │
│   ┌─────────────────────────────────────────┐                │
│   │ 3. 数据采集（复用 v0.2.0 引擎）          │                │
│   │   · xhs_scraper.py（笔记列表+元数据）    │                │
│   │   · ocr_images.sh（图文 OCR）            │                │
│   │   · transcribe_video.sh（视频 ASR）      │                │
│   └─────────────────────────────────────────┘                │
│        ↓                                                     │
│   ┌─────────────────────────────────────────┐                │
│   │ 4. 数据加工                              │                │
│   │   · AI 归类 top3 评论（带证据）           │                │
│   │   · 爆文判定（按粉丝量阈值）              │                │
│   │   · 半年外笔记 → _archive/               │                │
│   └─────────────────────────────────────────┘                │
│        ↓                                                     │
│   ┌─────────────────────────────────────────┐                │
│   │ 5. 落盘 + 报告                           │                │
│   │   · README.md / notes/*.md / _meta.json │                │
│   │   · images/ 本地化                      │                │
│   │   · 回话给用户：摘要 + 路径               │                │
│   └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 依赖关系

| 用什么 | 来自 |
|---|---|
| 网页抓取 | 优先 `agent-reach`；页面交互用 `agent-browser`；登录态访问用 `bb-browser`；复用 v0.2.0 的 `xhs_scraper.py` |
| OCR 图片文字 | v0.2.0 的 `scripts/media/ocr_image.swift` + `ocr_images.sh` |
| ASR 视频字幕 | v0.2.0 的 `scripts/media/transcribe_video.sh`（Whisper） |
| 单笔记报告模板 | v0.2.0 的 `references/single-note-template.md`（扩展加新字段） |
| 博主报告模板 | v0.2.0 的 `references/author-analysis-template.md`（扩展加 10 列总览） |

### 3.2 关键 ask 节点（来自 C1 宪法）

| 时机 | 问题 | 默认选项 |
|---|---|---|
| 第一次见博主 | "要加入对标库吗？" | 是 / 否 / 先看更多再定 |
| 入库时 | "落盘到哪？" | `~/Documents/xhs-竞品分析/` / iCloud / 自定义 |
| 入库时 | "归到哪个行业？" | 从已有目录列出 / 新建 |
| 深抓时 | "顺手抓口播/图文版？" | 都要 / 仅口播 / 仅图文 / 不要 |
| 增量扫描发现差量 | "发现 N 篇新内容，要继续吗？" | 全量增量 / 仅新爆文 / 仅这篇 / 摘要再定 |
| 兜底没数据 | "本地没存 X，要不要去网上抓？" | 抓 / 跳过 / 取消 |

---

## 4 · 文件结构与文档模板

### 4.1 完整目录树（以姜饼探 AI 为例）

```
{storage_root}/                                    ← 默认 ~/Documents/xhs-竞品分析/
└── AI工具/                                        ← 行业分类
    └── 小红书-姜饼探AI/                            ← {平台}-{博主名}
        ├── README.md                              ← 入口 · 10 列总览
        ├── _meta.json                             ← 程序化元数据
        ├── notes/
        │   ├── 2025-11-15-github三步上手.md         ← 单篇深抓
        │   ├── 2025-11-08-claude-md怎么写.md
        │   └── _archive/                          ← 半年外自动归档
        │       └── 2024-12-XX-...md
        └── images/
            ├── covers/                            ← 封面（命名 = 笔记日期-slug）
            └── slides/{笔记slug}/                  ← 正文图按笔记分目录
```

### 4.2 命名约定

| 实体 | 格式 | 示例 |
|---|---|---|
| 行业目录 | 中文短词 | `AI工具` / `营养师` / `职场` |
| 博主目录 | `{平台}-{博主名}` | `小红书-姜饼探AI` |
| 博主撞名 | 追加 redId | `小红书-姜饼探AI-95475810861` |
| 笔记文件名 | `{YYYY-MM-DD}-{slug}.md` | `2025-11-15-github三步上手.md` |
| slug 规则 | 标题前 8 字 + 去空格 / 标点 | `github三步上手` |
| 封面图 | 同 slug 的 webp | `2025-11-15-github三步上手.webp` |

### 4.3 `README.md` 模板（用户视图）

```markdown
# 小红书 · 姜饼探AI · 竞品档案
> 行业：AI工具 · 平台：小红书 · 是否对标：✅
> 最后扫描：2026-05-28 14:30 · 下次建议：2026-06-04

## 博主画像
- **粉丝量**：1.5w（爆文阈值 = 5000 赞）
- **简介**：北邮网安 → 帝国理工 CS 硕士 / 工具测评 / 趋势解读
- **IP**：北京
- **小红书号**：95475810861
- **数据**：73 关注 / 1.5w 粉 / 11.2w 总赞
- **首次入库**：2026-05-28
- **数据可信度**：✅ 全部来自实际抓取，无 AI 推测

## 内容形式分布（自动统计）
| 形式 | 数量 | 占比 |
|---|---|---|
| 图文 | 38 | 76% |
| 视频 | 12 | 24% |

## 选题主题分布（AI 归纳 · 可改）
| 主题 | 篇数 | 爆文数 | 代表标题 |
|---|---|---|---|
| Claude Code 技巧 | 12 | 3 | Claude code 隐藏技巧… |
| GitHub / 工具教程 | 8 | 2 | 0 基础学 github… |

## 笔记总览表（10 列 · 按时间倒序 · 半年内）
| 日期 | 封面 | 标题 | 链接 | 形式 | 点赞 | 收藏 | 评论 | 是否爆文 | 详情 |
|---|---|---|---|---|---|---|---|---|---|
| 11-15 | ![](images/covers/2025-11-15-github三步上手.webp) | GitHub 三步上手 | [→](https://...?xsec_token=...) | 图文 | 13 | 2644 | 23 | ✅ | [详情](notes/2025-11-15-github三步上手.md) |

## 爆文榜（粉丝量 > 2000 阈值 = 5000 赞）
1. 从 0 到 1 学 AI｜0 基础学 github｜免费工具宝库 — 3.1w 赞
2. 从 0 到 1 学 AI｜用爬虫加速信息收集 — 3352 赞

## 评论区高频诉求 TOP 3（合并爆文样本 · 双轨 · 挂原文证据）
1. 求教程/求链接（~40%）
2. 学习焦虑共鸣（~30%）
3. 工具对比/求推荐（~30%）

## 你（用户）和这个博主的差异化空间
> 此段在 S5 完成后自动填充
```

### 4.4 `notes/{date}-{slug}.md` 单笔记模板

```markdown
---
date: 2025-11-15
title: 普通人学 AI 必看，GitHub 三步上手
url: https://xiaohongshu.com/discovery/item/...?xsec_token=...
likes: 13
collects: 2644
comments: 23
format: 图文
is_explosive: true
tags: [#人工智能, #大模型, #AI工具, #ai, #姜学长]
scraped_at: 2026-05-28T14:30:00+08:00
---

## 封面
![](../images/covers/2025-11-15-github三步上手.webp)

## 正文（OCR 提取 · 来源：14 张轮播）
（按 slide 顺序逐张转录）

## 评论 top 10（原文 · 锁定不修改）
1. "求 github 教程链接" — 32 赞
2. ...

## 评论 top 3 归类（AI 整理 · 可被你否决）
### ① 求教程 / 求链接（4 条）
- "求 github 教程链接" · 32 赞
- ...

## 可复用要素（AI 提炼 · 用户可否决）
- **钩子套路**：「普通人 + 三步上手」→ 降门槛承诺
- **视觉**：黑底荧光绿 GitHub 主题 → 强识别度
- **结构**：1 痛点 → 3 步骤 → 1 收藏钩子
```

### 4.5 `_meta.json` 模板（机器视图）

```json
{
  "schema_version": "1.0",
  "blogger": {
    "platform": "xhs",
    "name": "姜饼探AI",
    "redId": "95475810861",
    "userId": "672bcca5000000001c01bfed",
    "industry": "AI工具",
    "is_target": true,
    "first_seen": "2026-05-28",
    "fans_count_history": [
      {"date": "2026-05-28", "count": 15000}
    ],
    "profile_url": "https://xiaohongshu.com/user/profile/..."
  },
  "explosive_threshold": 5000,
  "scan_history": [
    {
      "date": "2026-05-28T14:30+08:00",
      "notes_scanned": 38,
      "notes_deep": 5,
      "new_explosive": 1
    }
  ],
  "notes_index": [
    {
      "file": "notes/2025-11-15-github三步上手.md",
      "slug": "github三步上手",
      "date": "2025-11-15",
      "title": "普通人学 AI 必看，GitHub 三步上手",
      "url": "https://...?xsec_token=...",
      "likes": 13,
      "collects": 2644,
      "comments": 23,
      "format": "图文",
      "is_explosive": true,
      "last_updated": "2026-05-28T14:30+08:00",
      "deep_scraped": true,
      "asr_extracted": false,
      "comments_disabled": false,
      "top_comments_path": "notes/2025-11-15-github三步上手.md#评论-top-10",
      "status": "active"
    }
  ]
}
```

---

## 5 · 触发流程（四个场景）

### 场景 1 · 新博主 · 发了单篇笔记链接

完整对话脚本（4 个 ask 节点）见 brainstorm 第 3 节。简化流程：

1. SKILL: 识别链接 + 检查库 → 提示"新博主"
2. SKILL: 抓单篇 + 出摘要
3. **ASK**: 入库吗？
4. **ASK**: 落盘路径？
5. **ASK**: 行业分类？
6. SKILL: 标准扫描中（实时进度）
7. **ASK**: 深抓口播/图文？
8. SKILL: 落盘完成 + 摘要 + 路径

### 场景 2 · 老博主 · 再发新链接

1. SKILL: 识别 + 检查库 → "已入库 · 上次扫描 N 天前"
2. SKILL: 对比 `_meta.json` 算差量
3. SKILL: 展示差量摘要（新发布 N 篇 / 涨幅大 M 篇 / 新爆文 K 篇）
4. **ASK**: 怎么处理？（全量增量 / 仅新爆文 / 仅这篇 / 摘要再定）
5. SKILL: 跑增量 + 更新 README + `_meta.json`

### 场景 3 · 短链 / 主页链接

- **短链** `xhslink.com/...` → 跳转后归场景 1
- **主页** `xiaohongshu.com/user/profile/...` → **ASK**: 直接入库 / 先看前 12 篇 / 取消

### 场景 4 · 不想入库

1. **ASK**: 加入对标库吗？ → 否
2. SKILL: 出单篇拆解报告
3. **ASK**: 报告存哪？（临时输出 / 默认临时区 / 自定义）

---

## 6 · 边界情况处理

| 情况 | skill 行为 |
|---|---|
| 评论关闭 | `_meta.json` 标 `comments_disabled: true`，README 显示"评论已关"，**不强行编 top3 类** |
| 视频笔记无字幕 | **ASK**: "跑 ASR？慢但准（30 秒/篇）/ 跳过用标题概括" |
| 链接失效（删稿） | `_meta.json` 标 `status: "deleted"`，保留快照，不再尝试重抓 |
| 网络/反爬中断 | 已抓部分先落盘；**ASK**: "完成 X/Y，继续 / 暂停 / 降速重试" |
| 同名博主歧义 | redId 是唯一键，名字撞用 `小红书-姜饼探AI-95475810861/` |
| 爆文阈值动态 | 粉丝 < 2000 → 阈值 1000 赞；≥ 2000 → 5000 赞；每次扫描重算粉丝量 |
| 用户原话保护 | 评论 top 10 原文写入 `notes/{slug}.md` 的"评论 top 10（原文 · 锁定不修改）"段；`_meta.json.notes_index[].top_comments_path` 记录段落锚点；永不被 AI 改写 |

---

## 7 · 配置 · 路径变量化

为支持"别人电脑也能跑"，skill 内部用变量，不写死绝对路径。

### 7.1 `~/.claude/skills/bela-xhs-analysis/user-config.json`

```json
{
  "schema_version": "1.0",
  "storage_root": "~/Documents/xhs-竞品分析",
  "persona_root": "~/Magic AI*/大力个人档案",
  "default_industry": null,
  "explosive_threshold_low": 1000,
  "explosive_threshold_high": 5000,
  "fans_threshold": 2000,
  "archive_after_days": 180,
  "scan_depth_default": "standard",
  "ask_on_each_scan": true
}
```

### 7.2 首次使用引导

skill 加载时检查 `user-config.json` 是否存在：
- **不存在** → 只 ASK 2 个最关键值（`storage_root` / `persona_root`），其他字段用安全默认值（爆文阈值 1000/5000、归档 180 天、扫描深度 standard、`ask_on_each_scan: true`），生成 config
- **存在** → 直接读取，不重复问
- `default_industry` 永远是 `null`，即使用户连续 10 次都选 "AI 工具"，也每次都问（守 C1 宪法"不擅自动手"）

### 7.3 slug 规则（命名歧义消除）

笔记 slug 生成规则：
1. 取标题前 12 个**有效字符**（汉字 / 字母 / 数字 / 中划线 / 下划线）
2. 去除所有空格、标点、emoji、`#` 话题符号、特殊符号
3. 末尾不留连接符
4. 撞名追加 `-2` `-3`（按时间戳排序）

示例：
- `"普通人学AI必看，GitHub三步上手"` → `普通人学AI必看GitHub三`（截断到 12 字）
- 实际取语义抓手优先：`github三步上手`（手动指定 slug 优先于规则截断，写入 YAML `slug:` 字段）

---

## 8 · 与下游 skill 联动协议

**核心契约**：S1 落盘后，所有下游 skill 通过 `_meta.json` 的结构化字段读数据，**不**直接 grep markdown。

```
S1 (对标博主库)
   ↓ 写出 _meta.json + notes/*.md + images/
   ↓
   ├─→ S2 (正文/口播抓取)
   │     读 notes/*.md 的 YAML front matter
   │     找 transcript: null 的 → 跑 ASR → 写回同文件
   │
   ├─→ S3 (多格式产出)
   │     传 notes/{file}.md 路径 → guizang-ppt-skill 生 PPT
   │                            → baoyu-xhs-images 生图卡
   │                            → docx skill 生 Word
   │
   ├─→ S5 (人设感知生产)
   │     读 _meta.json.notes_index 选爆文模板
   │     + 读 user-config.persona_root 拿用户人设
   │     → 生成符合用户口吻的同主题口播
   │
   └─→ S4 (跨设备路径)
         把 storage_root 整目录 sync 到 iCloud / GitHub / Notion
```

### 8.1 接口稳定性承诺

- `_meta.json` schema 变更必须有 `schema_version` 字段 + 迁移脚本
- `notes/*.md` YAML front matter 字段名 = S2/S3/S5 写死的依赖，**不许改名**（只能加，不能删/改）
- 文件夹命名 `{行业}/{平台}-{博主名}` 是 S4 同步的硬约定

---

## 9 · 验收标准（4 条宪法落地）

| 宪法 | 验收检查 |
|---|---|
| 🚫 C1 | 全流程 ⭐ ask 节点 ≥ 4 个，少一个 = fail |
| 🚫 C2 | 评论 top3 类的每一类必须挂 ≥ 2 条评论原文 + 点赞数 |
| ✅ C3 | `_meta.json` 必须记录：scraped_at / 原始 URL（带 xsec_token） / 本地图片相对路径 |
| ✅ C4 | README/笔记中的 AI 归纳段必须标"AI 整理 · 可被你否决"；禁用"震惊体""绝绝子""家人们" |

### 9.1 测试用例

| # | 输入 | 预期结果 | 通过判定 |
|---|---|---|---|
| T1 | 新博主单篇笔记链接 | 走场景 1，触发 4 个 ask，落盘成完整目录 | 文件树完整 + 评论挂证据 |
| T2 | 同一链接再发一次 | 走场景 2 增量 | `_meta.json.scan_history` 多一条 |
| T3 | 短链 `xhslink.com/...` | 解析后归 T1 | 实际 URL 解析成功 |
| T4 | 主页链接 | ASK"先看 / 直接入库 / 取消" | 不强行抓全量 |
| T5 | 选"否，不入库" | 临时报告，不写入对标库目录 | `storage_root` 不新增博主文件夹 |
| T6 | 评论区关闭的博主 | README 标"评论已关"，不编 top3 类 | 没有 AI 编造的分类 |
| T7 | 中途网络中断 | 已抓部分落盘 + ASK 继续/暂停 | 没有半成品脏数据 |
| T8 | 半年外的老笔记 | 自动归到 `notes/_archive/`，主表干净 | 主表只有半年内 |

---

## 10 · 实施范围（v0.2.0 → v0.3.0）

### 10.1 新增文件

```
~/.claude/skills/bela-xhs-analysis/
├── SKILL.md                                       ← 升级到 v0.3.0，加 S1 模块
├── user-config.json                               ← 新增·路径变量化
├── references/
│   ├── competitor-library-flow.md                 ← 新增·四场景完整对话脚本
│   ├── meta-json-schema.md                        ← 新增·_meta.json 字段说明
│   └── readme-template.md                         ← 新增·README 自动生成模板
└── scripts/
    ├── library/
    │   ├── init_blogger.py                        ← 新增·首次入库
    │   ├── incremental_scan.py                    ← 新增·增量扫描
    │   ├── archive_old.py                         ← 新增·半年归档
    │   ├── render_readme.py                       ← 新增·README 自动渲染
    │   └── classify_comments.py                   ← 新增·评论双轨归类
    └── (复用 v0.2.0 的 xhs_scraper.py / media/*.sh)
```

### 10.2 修改文件

| 文件 | 修改内容 |
|---|---|
| `SKILL.md` | v0.2.0 → v0.3.0；触发逻辑加"库内检查"；新增 S1 章节 |
| `references/author-analysis-template.md` | 加 10 列总览表 + 双轨评论格式 |
| `references/single-note-template.md` | 加 YAML front matter 标准字段 |
| `scripts/xhs_scraper.py` | 加 profile 模式（抓主页近半年笔记列表） |

### 10.3 不动文件

- `scripts/media/*`（OCR/ASR 引擎不变）
- `LICENSE / README.md / README.zh.md`（仅版本号小升）
- `install.sh`（已 OK）

---

## 11 · 风险与缓解

| 风险 | 缓解 |
|---|---|
| 小红书反爬升级，xsec_token 失效 | 复用 v0.2.0 已有的 `cookie-setup-guide.md`；reading 失败时给用户清晰错误提示 |
| 增量扫描算法判定错误（漏算/重算） | 用 `_meta.json.scan_history` 作为唯一 source of truth；每次扫描记录 timestamp |
| 评论 AI 归类违反"不幻觉"宪法 | C2 已规定每类挂 ≥ 2 条原文证据；无法归类时如实标注"无法归类，请见原文" |
| 用户 `storage_root` 改动后老数据失联 | `user-config.json` 有 schema_version；改路径时给迁移脚本（手动 mv） |
| 评论数太少（< 10 条）无法做 top3 类 | 评论 < 10 时不做归类，README 直接列原文 + 标注"评论较少，未做归类" |

---

## 12 · 后续 spec 队列

| spec | 内容 | 预估 |
|---|---|---|
| S2 | 正文/口播抓取增强（v0.2.0 已部分实现，需要查漏补缺） | 1 份 spec |
| S3 | 多格式产出（MD → PPT / HTML / Word / 图卡） | 1 份 spec |
| S5 | 人设感知生产（含"用户没特点怎么引导"五问问卷） | 1 份 spec |
| S4 | 跨设备路径策略（iCloud / GitHub / Notion） | 1 份 spec |

---

## 13 · 审批 · 用户 sign-off

| 项 | 状态 |
|---|---|
| 设计宪法 5 条 | ✅ 用户确认（2026-05-28 brainstorm） |
| 五个核心决策（D1-D5） | ✅ 用户选定 B/B/B/B/C |
| 四节设计（架构/文件/触发/验收） | ✅ 用户逐节 OK |
| spec 落盘路径 | ✅ A（跟着 skill 走） |
| spec 文件最终 review | ⏳ 待用户 review 本文件 |
| 进入 writing-plans 阶段 | ⏳ 待 review 通过 |
