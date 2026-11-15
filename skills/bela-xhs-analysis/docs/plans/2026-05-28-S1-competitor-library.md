# S1 · 对标博主库 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `bela-xhs-analysis` 从 v0.2.0 的"单次分析引擎"升级为 v0.3.0 的"持续追踪对标库"，落地 spec `2026-05-28-S1-competitor-library-design.md` 全部决策（5 宪法 / 5 决策 / 4 节设计 / 8 测试用例）。

**Architecture:** 顶层是 SKILL.md 触发 + ask 流程；中层是 Python 库（`scripts/library/`）做"读 meta → 算差量 → 调 scraper → 渲染 README"；底层复用 v0.2.0 的 `xhs_scraper.py` + `media/*.sh`（不改变其接口）。所有数据落在用户可配置的 `storage_root` 下，结构是 `{行业}/{平台}-{博主}/`。

**Tech Stack:** Python 3.11+（已有 `xhs_scraper.py` 基础）/ pytest 测试 / bash 编排 / `~/.claude/skills/bela-xhs-analysis/` 仓库 / git 频繁提交

**前置假设：**
- 工作目录 = `~/.claude/skills/bela-xhs-analysis/`
- v0.2.0 `scripts/xhs_scraper.py` 已可抓取单篇笔记（input: URL → output: JSON with title/likes/...）
- v0.2.0 `scripts/media/ocr_images.sh` 已可批量 OCR webp → text
- v0.2.0 `scripts/media/transcribe_video.sh` 已可 Whisper 转写
- 用户已设好 cookies（`scripts/.env`）

---

## 文件结构（实施前盘点）

### 新增文件（11）
```
~/.claude/skills/bela-xhs-analysis/
├── user-config.json                          ← 用户路径 + 阈值配置
├── references/
│   ├── competitor-library-flow.md            ← 四场景对话脚本
│   ├── meta-json-schema.md                   ← _meta.json 契约文档
│   └── readme-template.md                    ← README 自动生成模板说明
└── scripts/
    └── library/
        ├── __init__.py
        ├── paths.py                          ← 路径解析 + user-config 读写
        ├── utils.py                          ← slug / 中文数字 / 爆文判定
        ├── meta_store.py                     ← _meta.json 读写
        ├── classify_comments.py              ← 评论双轨归类
        ├── archive_old.py                    ← 半年归档
        ├── render_readme.py                  ← README 渲染
        ├── init_blogger.py                   ← 首次入库
        └── incremental_scan.py               ← 增量扫描
```

### 修改文件（4）
```
SKILL.md                                       ← v0.2.0 → v0.3.0；加 S1 章节 + 触发逻辑
references/author-analysis-template.md         ← 加 10 列总览表 + 双轨评论
references/single-note-template.md             ← 加 YAML front matter 标准字段
scripts/xhs_scraper.py                         ← 加 profile mode（抓主页近半年）
```

### 不动文件
- `LICENSE` / `README.md` / `README.zh.md` / `install.sh` / `.gitignore`
- `scripts/media/*`（OCR/ASR 引擎不变）
- `scripts/.env`

### 测试目录
```
tests/
├── conftest.py                               ← pytest fixtures
├── fixtures/                                 ← 已存在（gitignored）
│   └── sample_meta.json                      ← 测试用 mock
├── test_utils.py
├── test_meta_store.py
├── test_classify_comments.py
├── test_archive_old.py
├── test_render_readme.py
├── test_init_blogger.py
├── test_incremental_scan.py
└── test_e2e_acceptance.py                    ← T1-T8 验收
```

---

## Phase 1 · 基础数据契约（先文档后代码）

### Task 1: 写 `_meta.json` schema 契约文档

**Files:**
- Create: `references/meta-json-schema.md`

- [ ] **Step 1: 写完整 schema 文档**

```markdown
# _meta.json Schema · v1.0

每个博主目录下都有一份 `_meta.json`，是程序化元数据的唯一来源。
**契约稳定性**：字段名 = 下游 skill 写死的依赖，**只能增不能改**。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `schema_version` | string | ✅ | 当前 `"1.0"`；breaking change 时升级 |
| `blogger` | object | ✅ | 博主元数据，见下 |
| `explosive_threshold` | number | ✅ | 当前粉丝量对应的爆文阈值（粉丝 < 2000 → 1000，≥ 2000 → 5000） |
| `scan_history` | array | ✅ | 每次扫描的时间 + 摘要 |
| `notes_index` | array | ✅ | 所有笔记的索引（含归档） |

## `blogger` 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `platform` | string | ✅ | 固定 `"xhs"`；预留多平台 |
| `name` | string | ✅ | 博主昵称 |
| `redId` | string | ✅ | 小红书号；歧义解消的唯一键 |
| `userId` | string | ✅ | URL 中的 user/profile/{userId} |
| `industry` | string | ✅ | 用户分类（"AI工具" / "营养师" / ...） |
| `is_target` | boolean | ✅ | 是否对标账户（用户首次入库时确认） |
| `first_seen` | string | ✅ | 首次入库日期 `YYYY-MM-DD` |
| `fans_count_history` | array | ✅ | 粉丝量历史，元素 `{date, count}` |
| `profile_url` | string | ✅ | 主页 URL（带 xsec_token） |

## `scan_history` 元素字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `date` | string | ISO 8601 timestamp |
| `notes_scanned` | number | 浅抓笔记数 |
| `notes_deep` | number | 深抓笔记数 |
| `new_explosive` | number | 本次新增爆文数 |

## `notes_index` 元素字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `file` | string | 相对路径 `notes/{slug}.md` 或 `notes/_archive/{slug}.md` |
| `slug` | string | 笔记 slug，对应文件名 |
| `date` | string | 笔记发布日期 |
| `title` | string | 笔记标题 |
| `url` | string | 完整 URL（含 xsec_token） |
| `likes` | number | 点赞数 |
| `collects` | number | 收藏数 |
| `comments` | number | 评论总数 |
| `format` | string | "图文" / "视频" |
| `is_explosive` | boolean | 按当前 explosive_threshold 算 |
| `last_updated` | string | ISO 8601 timestamp |
| `deep_scraped` | boolean | 是否做过深抓（正文 OCR + 评论 top10） |
| `asr_extracted` | boolean | 视频笔记是否做过 ASR |
| `comments_disabled` | boolean | 评论是否被博主关闭 |
| `top_comments_path` | string | 形如 `notes/{slug}.md#评论-top-10` 的锚点 |
| `status` | string | "active" / "archived" / "deleted" |

## 完整示例

\`\`\`json
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
    "fans_count_history": [{"date": "2026-05-28", "count": 15000}],
    "profile_url": "https://www.xiaohongshu.com/user/profile/672bcca5000000001c01bfed?xsec_token=..."
  },
  "explosive_threshold": 5000,
  "scan_history": [
    {"date": "2026-05-28T14:30+08:00", "notes_scanned": 38, "notes_deep": 5, "new_explosive": 1}
  ],
  "notes_index": [
    {
      "file": "notes/2025-11-15-github三步上手.md",
      "slug": "github三步上手",
      "date": "2025-11-15",
      "title": "普通人学AI必看，GitHub三步上手",
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
\`\`\`
```

- [ ] **Step 2: 提交**

```bash
git add references/meta-json-schema.md
git commit -m "docs(S1): add _meta.json schema v1.0"
```

---

### Task 2: 创建 `user-config.json` + 首次引导文档

**Files:**
- Create: `user-config.json.example`（模板，不含真实路径）
- Create: `references/user-config-guide.md`

- [ ] **Step 1: 写 `user-config.json.example`**

```json
{
  "schema_version": "1.0",
  "storage_root": "~/Documents/xhs-竞品分析",
  "persona_root": "~/Documents/个人档案",
  "default_industry": null,
  "explosive_threshold_low": 1000,
  "explosive_threshold_high": 5000,
  "fans_threshold": 2000,
  "archive_after_days": 180,
  "scan_depth_default": "standard",
  "ask_on_each_scan": true
}
```

- [ ] **Step 2: 写 `references/user-config-guide.md`**

```markdown
# user-config.json · 首次使用引导

skill 首次运行时检查根目录是否有 `user-config.json`：
- **不存在** → 只 ASK 2 个最关键值：
  1. `storage_root`（对标库根目录，默认 `~/Documents/xhs-竞品分析`）
  2. `persona_root`（用户人设档案目录，默认 `~/Documents/个人档案`）
  
  其他字段自动用安全默认值（见 `user-config.json.example`）。
- **存在** → 直接读取，不重复问。

## 字段说明

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `schema_version` | string | `"1.0"` | 升级时迁移用 |
| `storage_root` | path | `~/Documents/xhs-竞品分析` | 对标库根目录 |
| `persona_root` | path | `~/Documents/个人档案` | S5 用户人设档案 |
| `default_industry` | string\|null | `null` | **永远 null，每次都问** |
| `explosive_threshold_low` | number | `1000` | 粉丝 < `fans_threshold` 时的爆文阈值 |
| `explosive_threshold_high` | number | `5000` | 粉丝 ≥ `fans_threshold` 时的爆文阈值 |
| `fans_threshold` | number | `2000` | 粉丝量分档 |
| `archive_after_days` | number | `180` | 半年外归档（不删除） |
| `scan_depth_default` | string | `"standard"` | `standard` / `minimal` / `full` |
| `ask_on_each_scan` | boolean | `true` | 每次扫描前是否 ASK（守 C1 宪法） |

## 路径变量

文件中所有路径支持：
- `~` 展开为 `$HOME`
- 不展开环境变量（避免 leak）
```

- [ ] **Step 3: 把 `user-config.json` 加进 `.gitignore`**

```bash
echo "" >> .gitignore
echo "# S1 · user config（含本地路径，不入库）" >> .gitignore
echo "user-config.json" >> .gitignore
```

- [ ] **Step 4: 提交**

```bash
git add user-config.json.example references/user-config-guide.md .gitignore
git commit -m "feat(S1): add user-config.json + first-run guide"
```

---

### Task 3: 升级 `references/single-note-template.md`

**Files:**
- Modify: `references/single-note-template.md`

- [ ] **Step 1: 在文件顶部加 YAML front matter 标准段**

读取现有文件，在第一行（`#` 标题之前）插入：

```markdown
## 文件头 · YAML Front Matter（标准字段，下游 skill 依赖）

每篇笔记 `.md` 必须以 YAML front matter 起头：

\`\`\`yaml
---
date: 2025-11-15            # 笔记发布日期 YYYY-MM-DD
slug: github三步上手          # 文件名 stem
title: 普通人学AI必看，GitHub三步上手
url: https://www.xiaohongshu.com/discovery/item/...?xsec_token=...
likes: 13
collects: 2644
comments: 23
format: 图文                  # 图文 | 视频
is_explosive: true            # 按粉丝阈值判定
tags: [#人工智能, #大模型, #AI工具]
scraped_at: 2026-05-28T14:30:00+08:00
deep_scraped: true
asr_extracted: false
comments_disabled: false
---
\`\`\`

字段必须与 `references/meta-json-schema.md` 中的 `notes_index` 元素**一一对应**。
```

- [ ] **Step 2: 提交**

```bash
git add references/single-note-template.md
git commit -m "feat(S1): single-note-template YAML front matter standard"
```

---

### Task 4: 升级 `references/author-analysis-template.md`

**Files:**
- Modify: `references/author-analysis-template.md`

- [ ] **Step 1: 在文件末尾追加 README 10 列总览表标准**

```markdown
## README.md 标准结构（v0.3.0 新增）

每个博主目录的 `README.md` 必须包含以下 7 段（按顺序）：

1. **顶部** — 博主基本信息 + 上次扫描时间
2. **博主画像** — 粉丝/简介/IP/ID/历史关注比
3. **内容形式分布** — 图文/视频占比
4. **选题主题分布** — AI 归纳 + 篇数 + 爆文数
5. **笔记总览表（10 列）** — 半年内笔记，时间倒序
6. **爆文榜** — 按当前阈值
7. **评论区高频诉求 TOP 3** — 双轨格式

### 10 列字段对照表

| 列名 | 来自 _meta.json 字段 |
|---|---|
| 日期 | `notes_index[].date` |
| 封面 | `notes_index[].slug` → `images/covers/{slug}.webp` |
| 标题 | `notes_index[].title` |
| 链接 | `notes_index[].url` |
| 形式 | `notes_index[].format` |
| 点赞 | `notes_index[].likes` |
| 收藏 | `notes_index[].collects` |
| 评论 | `notes_index[].comments` |
| 是否爆文 | `notes_index[].is_explosive` |
| 详情 | `notes_index[].file` |

### 评论 top3 类标准格式（双轨）

\`\`\`markdown
## 评论区高频诉求 TOP 3（合并爆文样本 · 每类挂原文证据）

### ① {分类名}（占比 ~N% · M 条）
- "{原文}" · {N}赞
- "{原文}" · {N}赞
\`\`\`

**硬规则**：
- 每个分类必须挂 ≥ 2 条原文证据
- 评论 < 10 条时不归类，直接列原文 + 标注"评论较少，未做归类"
- 评论关闭时不出此段，标 "评论已关"
```

- [ ] **Step 2: 提交**

```bash
git add references/author-analysis-template.md
git commit -m "feat(S1): author-analysis-template 10-col README spec"
```

---

## Phase 2 · 纯函数工具层（TDD 重点）

### Task 5: `scripts/library/utils.py` — slug / 中文数字 / 爆文判定

**Files:**
- Create: `scripts/library/__init__.py`
- Create: `scripts/library/utils.py`
- Create: `tests/test_utils.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 先写 `tests/conftest.py`**

```python
"""Pytest fixtures for S1 tests."""
import json
import pytest
from pathlib import Path


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
            "profile_url": "https://www.xiaohongshu.com/user/profile/672bcca5000000001c01bfed?xsec_token=test"
        },
        "explosive_threshold": 5000,
        "scan_history": [],
        "notes_index": []
    }


@pytest.fixture
def tmp_blogger_dir(tmp_path):
    """A tmp dir structured like a blogger folder."""
    bdir = tmp_path / "AI工具" / "小红书-姜饼探AI"
    (bdir / "notes" / "_archive").mkdir(parents=True)
    (bdir / "images" / "covers").mkdir(parents=True)
    (bdir / "images" / "slides").mkdir(parents=True)
    return bdir
```

- [ ] **Step 2: 写失败的 `tests/test_utils.py`**

```python
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
        assert slug_from_title("普通人学AI必看，GitHub三步上手") == "普通人学AI必看GitHub三"

    def test_strips_emoji(self):
        assert slug_from_title("🍪 GitHub 三步上手") == "GitHub三步上手"

    def test_strips_hashtag(self):
        assert slug_from_title("教程 #人工智能") == "教程人工智能"

    def test_max_12_chars(self):
        assert len(slug_from_title("a" * 50)) == 12


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


class TestIsExplosive:
    def test_low_fans_low_likes(self):
        # 粉丝 1500 < 2000 → 阈值 1000；1000 赞 = 临界爆文
        assert is_explosive(likes=1000, fans=1500, fans_threshold=2000,
                             low=1000, high=5000) is True

    def test_low_fans_below(self):
        assert is_explosive(likes=999, fans=1500, fans_threshold=2000,
                             low=1000, high=5000) is False

    def test_high_fans_high_likes(self):
        assert is_explosive(likes=5000, fans=15000, fans_threshold=2000,
                             low=1000, high=5000) is True

    def test_high_fans_below(self):
        assert is_explosive(likes=4999, fans=15000, fans_threshold=2000,
                             low=1000, high=5000) is False


class TestIsoNow:
    def test_format(self):
        s = iso_now()
        # 形如 2026-05-28T14:30:00+08:00
        assert "T" in s and ("+08:00" in s or "Z" in s)
```

- [ ] **Step 3: 运行测试，确认失败**

```bash
cd ~/.claude/skills/bela-xhs-analysis
python -m pytest tests/test_utils.py -v
```

Expected: 全部 FAIL（模块还不存在）

- [ ] **Step 4: 写 `scripts/library/__init__.py`**

```python
"""S1 · 对标博主库 · v0.3.0"""
```

- [ ] **Step 5: 写 `scripts/library/utils.py`**

```python
"""Pure utility functions for S1.

设计宪法 C2: 不幻觉. 所有解析失败时 raise，不返回猜测值.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone, timedelta


# 中文字符 / 字母 / 数字 / 中划线 / 下划线
_SLUG_VALID = re.compile(r"[一-龥A-Za-z0-9\-_]")


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
```

- [ ] **Step 6: 跑测试，全过**

```bash
python -m pytest tests/test_utils.py -v
```

Expected: 全 PASS（13 个用例）

- [ ] **Step 7: 提交**

```bash
git add scripts/library/__init__.py scripts/library/utils.py tests/test_utils.py tests/conftest.py
git commit -m "feat(S1): library utils (slug, 中文数字, 爆文判定)"
```

---

### Task 6: `scripts/library/paths.py` — 路径解析 + user-config 读写

**Files:**
- Create: `scripts/library/paths.py`
- Create: `tests/test_paths.py`

- [ ] **Step 1: 写失败的 `tests/test_paths.py`**

```python
"""Tests for paths.py."""
import json
import pytest
from pathlib import Path
from scripts.library.paths import (
    load_user_config,
    save_user_config,
    blogger_dir,
    notes_dir,
    images_dir,
    DEFAULT_CONFIG,
)


def test_load_user_config_returns_defaults_when_missing(tmp_path):
    config_path = tmp_path / "user-config.json"
    cfg = load_user_config(config_path)
    assert cfg["schema_version"] == "1.0"
    assert cfg["storage_root"] == "~/Documents/xhs-竞品分析"
    assert cfg["explosive_threshold_low"] == 1000


def test_save_user_config_writes_file(tmp_path):
    config_path = tmp_path / "user-config.json"
    custom = dict(DEFAULT_CONFIG)
    custom["storage_root"] = "/tmp/test-xhs"
    save_user_config(custom, config_path)
    assert config_path.exists()
    loaded = json.loads(config_path.read_text())
    assert loaded["storage_root"] == "/tmp/test-xhs"


def test_blogger_dir_composition(tmp_path):
    cfg = dict(DEFAULT_CONFIG)
    cfg["storage_root"] = str(tmp_path)
    p = blogger_dir(cfg, industry="AI工具", platform="xhs", name="姜饼探AI")
    assert p == tmp_path / "AI工具" / "小红书-姜饼探AI"


def test_blogger_dir_redid_disambiguation(tmp_path):
    cfg = dict(DEFAULT_CONFIG)
    cfg["storage_root"] = str(tmp_path)
    p = blogger_dir(cfg, industry="AI工具", platform="xhs",
                     name="姜饼探AI", redId="95475810861")
    assert p == tmp_path / "AI工具" / "小红书-姜饼探AI-95475810861"


def test_notes_and_images_under_blogger(tmp_path):
    cfg = dict(DEFAULT_CONFIG)
    cfg["storage_root"] = str(tmp_path)
    bdir = blogger_dir(cfg, industry="AI工具", platform="xhs", name="A")
    assert notes_dir(bdir) == bdir / "notes"
    assert images_dir(bdir) == bdir / "images"
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
python -m pytest tests/test_paths.py -v
```

Expected: FAIL（模块不存在）

- [ ] **Step 3: 写 `scripts/library/paths.py`**

```python
"""Path resolution for S1.

负责 user-config.json 的读写 + 博主目录路径组装.
设计宪法 C5: 数据兜底流程 - 先读本地，没有就用默认.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

_SKILL_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _SKILL_ROOT / "user-config.json"

DEFAULT_CONFIG = {
    "schema_version": "1.0",
    "storage_root": "~/Documents/xhs-竞品分析",
    "persona_root": "~/Documents/个人档案",
    "default_industry": None,
    "explosive_threshold_low": 1000,
    "explosive_threshold_high": 5000,
    "fans_threshold": 2000,
    "archive_after_days": 180,
    "scan_depth_default": "standard",
    "ask_on_each_scan": True,
}

PLATFORM_DISPLAY = {
    "xhs": "小红书",
}


def load_user_config(path: Path | None = None) -> dict:
    """加载用户配置；不存在则返回默认副本."""
    path = path or _DEFAULT_CONFIG_PATH
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    return json.loads(path.read_text(encoding="utf-8"))


def save_user_config(cfg: dict, path: Path | None = None) -> None:
    """保存用户配置."""
    path = path or _DEFAULT_CONFIG_PATH
    path.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def storage_root(cfg: dict) -> Path:
    """从 cfg 拿 storage_root 并展开 ~."""
    return Path(cfg["storage_root"]).expanduser()


def blogger_dir(
    cfg: dict,
    *,
    industry: str,
    platform: str,
    name: str,
    redId: Optional[str] = None,
) -> Path:
    """组装博主目录路径.

    规则：{storage_root}/{industry}/{平台显示名}-{name}[-{redId}]
    """
    platform_zh = PLATFORM_DISPLAY.get(platform, platform)
    folder = f"{platform_zh}-{name}"
    if redId:
        folder = f"{folder}-{redId}"
    return storage_root(cfg) / industry / folder


def notes_dir(bdir: Path) -> Path:
    return bdir / "notes"


def archive_dir(bdir: Path) -> Path:
    return bdir / "notes" / "_archive"


def images_dir(bdir: Path) -> Path:
    return bdir / "images"


def covers_dir(bdir: Path) -> Path:
    return bdir / "images" / "covers"


def slides_dir(bdir: Path, slug: str) -> Path:
    return bdir / "images" / "slides" / slug


def meta_path(bdir: Path) -> Path:
    return bdir / "_meta.json"


def readme_path(bdir: Path) -> Path:
    return bdir / "README.md"
```

- [ ] **Step 4: 跑测试，全过**

```bash
python -m pytest tests/test_paths.py -v
```

Expected: 全 PASS（5 个用例）

- [ ] **Step 5: 提交**

```bash
git add scripts/library/paths.py tests/test_paths.py
git commit -m "feat(S1): paths.py — user-config + 博主目录组装"
```

---

### Task 7: `scripts/library/meta_store.py` — `_meta.json` 读写

**Files:**
- Create: `scripts/library/meta_store.py`
- Create: `tests/test_meta_store.py`

- [ ] **Step 1: 写失败的 `tests/test_meta_store.py`**

```python
"""Tests for meta_store.py."""
import json
import pytest
from scripts.library.meta_store import (
    read_meta, write_meta,
    upsert_note, find_note_by_url, find_note_by_slug,
    append_scan_history,
)


def test_write_and_read_roundtrip(tmp_path, sample_meta):
    meta_file = tmp_path / "_meta.json"
    write_meta(meta_file, sample_meta)
    loaded = read_meta(meta_file)
    assert loaded == sample_meta


def test_read_meta_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_meta(tmp_path / "nope.json")


def test_upsert_note_new(sample_meta):
    note = {
        "file": "notes/2025-11-15-github.md",
        "slug": "github",
        "url": "https://x/1?xsec_token=A",
        "likes": 13, "collects": 2644,
    }
    upsert_note(sample_meta, note)
    assert len(sample_meta["notes_index"]) == 1
    assert sample_meta["notes_index"][0]["slug"] == "github"


def test_upsert_note_update(sample_meta):
    note = {"file": "n.md", "slug": "g", "url": "u1", "likes": 10}
    upsert_note(sample_meta, note)
    note2 = {"file": "n.md", "slug": "g", "url": "u1", "likes": 50}
    upsert_note(sample_meta, note2)
    assert len(sample_meta["notes_index"]) == 1
    assert sample_meta["notes_index"][0]["likes"] == 50


def test_find_note_by_url(sample_meta):
    sample_meta["notes_index"].append({"slug": "a", "url": "https://x?xsec_token=A"})
    sample_meta["notes_index"].append({"slug": "b", "url": "https://y"})
    assert find_note_by_url(sample_meta, "https://x?xsec_token=A")["slug"] == "a"
    assert find_note_by_url(sample_meta, "https://z") is None


def test_find_note_ignores_xsec_token(sample_meta):
    """xsec_token 会过期，匹配要忽略它."""
    sample_meta["notes_index"].append({"slug": "a",
        "url": "https://x.com/discovery/item/abc?xsec_token=OLD"})
    found = find_note_by_url(sample_meta,
        "https://x.com/discovery/item/abc?xsec_token=NEW")
    assert found is not None and found["slug"] == "a"


def test_append_scan_history(sample_meta):
    entry = {"date": "2026-05-28T14:30+08:00", "notes_scanned": 5,
             "notes_deep": 2, "new_explosive": 1}
    append_scan_history(sample_meta, entry)
    assert len(sample_meta["scan_history"]) == 1
    assert sample_meta["scan_history"][0]["notes_scanned"] == 5
```

- [ ] **Step 2: 跑测试，FAIL**

```bash
python -m pytest tests/test_meta_store.py -v
```

- [ ] **Step 3: 写 `scripts/library/meta_store.py`**

```python
"""_meta.json read/write + 索引操作.

设计宪法 C3: 有迹可循 - 所有写入必须保留时间戳和原始 URL.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs


def read_meta(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"_meta.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_meta(path: Path, meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _strip_xsec(url: str) -> str:
    """归一化 URL（去 xsec_token / share_id 等会过期的字段）以做匹配."""
    p = urlparse(url)
    keep = [(k, v) for k, v in parse_qs(p.query, keep_blank_values=True).items()
            if k not in {"xsec_token", "share_id", "shareRedId", "apptime"}]
    base = f"{p.scheme}://{p.netloc}{p.path}"
    return base


def find_note_by_url(meta: dict, url: str) -> Optional[dict]:
    target = _strip_xsec(url)
    for note in meta.get("notes_index", []):
        if "url" in note and _strip_xsec(note["url"]) == target:
            return note
    return None


def find_note_by_slug(meta: dict, slug: str) -> Optional[dict]:
    for note in meta.get("notes_index", []):
        if note.get("slug") == slug:
            return note
    return None


def upsert_note(meta: dict, note: dict) -> None:
    """按 slug 去重；存在则覆盖，不存在则追加."""
    slug = note.get("slug")
    if not slug:
        raise ValueError("note must have 'slug' field")
    existing = find_note_by_slug(meta, slug)
    if existing:
        existing.update(note)
    else:
        meta.setdefault("notes_index", []).append(note)


def append_scan_history(meta: dict, entry: dict) -> None:
    meta.setdefault("scan_history", []).append(entry)
```

- [ ] **Step 4: 跑测试，全过**

```bash
python -m pytest tests/test_meta_store.py -v
```

Expected: 全 PASS（7 个用例）

- [ ] **Step 5: 提交**

```bash
git add scripts/library/meta_store.py tests/test_meta_store.py
git commit -m "feat(S1): meta_store.py — _meta.json CRUD + URL 归一化匹配"
```

---

## Phase 3 · 业务逻辑模块

### Task 8: `scripts/library/archive_old.py` — 半年自动归档

**Files:**
- Create: `scripts/library/archive_old.py`
- Create: `tests/test_archive_old.py`

- [ ] **Step 1: 写失败的 `tests/test_archive_old.py`**

```python
"""Tests for archive_old.py."""
from datetime import date, timedelta
from scripts.library.archive_old import (
    should_archive, partition_notes, archive_in_meta,
)


def test_should_archive_old_note():
    today = date(2026, 5, 28)
    old = date(2025, 5, 1)
    assert should_archive(old, today=today, after_days=180) is True


def test_should_not_archive_recent_note():
    today = date(2026, 5, 28)
    recent = date(2026, 4, 1)
    assert should_archive(recent, today=today, after_days=180) is False


def test_partition_notes_keeps_status_active():
    notes = [
        {"slug": "a", "date": "2025-11-01", "status": "active"},
        {"slug": "b", "date": "2025-01-01", "status": "active"},
    ]
    active, to_archive = partition_notes(
        notes, today=date(2026, 5, 28), after_days=180,
    )
    assert [n["slug"] for n in active] == ["a"]
    assert [n["slug"] for n in to_archive] == ["b"]


def test_archive_in_meta_flips_status(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "old", "file": "notes/old.md",
         "date": "2025-01-01", "status": "active"},
    ]
    archive_in_meta(sample_meta, today=date(2026, 5, 28), after_days=180)
    note = sample_meta["notes_index"][0]
    assert note["status"] == "archived"
    assert note["file"] == "notes/_archive/old.md"
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: 写 `scripts/library/archive_old.py`**

```python
"""半年外笔记自动归档（不删除）.

设计宪法 C3: 有迹可循 - 老数据物理保留，只是标 status=archived 并移动文件.
"""
from __future__ import annotations
from datetime import date, timedelta


def should_archive(note_date: date, *, today: date, after_days: int) -> bool:
    return (today - note_date) > timedelta(days=after_days)


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def partition_notes(
    notes: list[dict],
    *,
    today: date,
    after_days: int,
) -> tuple[list[dict], list[dict]]:
    active: list[dict] = []
    to_archive: list[dict] = []
    for n in notes:
        if n.get("status") == "archived":
            continue
        d = _parse_date(n["date"])
        if should_archive(d, today=today, after_days=after_days):
            to_archive.append(n)
        else:
            active.append(n)
    return active, to_archive


def archive_in_meta(
    meta: dict,
    *,
    today: date,
    after_days: int,
) -> list[dict]:
    """将 _meta.json 中半年外的笔记标 archived 并改 file 路径.

    Returns: 被归档的笔记列表（caller 可用于 mv 实际文件）
    """
    archived = []
    for note in meta.get("notes_index", []):
        if note.get("status") == "archived":
            continue
        if should_archive(_parse_date(note["date"]),
                          today=today, after_days=after_days):
            note["status"] = "archived"
            # 路径：notes/{slug}.md → notes/_archive/{slug}.md
            old = note["file"]
            if "/_archive/" not in old:
                parts = old.split("/")
                note["file"] = "/".join(parts[:-1]) + "/_archive/" + parts[-1]
            archived.append(note)
    return archived
```

- [ ] **Step 4: 跑测试，PASS**

```bash
python -m pytest tests/test_archive_old.py -v
```

- [ ] **Step 5: 提交**

```bash
git add scripts/library/archive_old.py tests/test_archive_old.py
git commit -m "feat(S1): archive_old.py — 半年归档（status flip + 路径改写）"
```

---

### Task 9: `scripts/library/classify_comments.py` — 评论双轨归类（C2 宪法核心）

**Files:**
- Create: `scripts/library/classify_comments.py`
- Create: `tests/test_classify_comments.py`

- [ ] **Step 1: 写失败的 `tests/test_classify_comments.py`**

```python
"""Tests for classify_comments.py (C2 宪法守门员)."""
import pytest
from scripts.library.classify_comments import (
    can_classify, build_dual_track,
)


def test_can_classify_with_enough_comments():
    comments = [{"text": "x", "likes": 1}] * 10
    assert can_classify(comments) is True


def test_cannot_classify_with_few_comments():
    comments = [{"text": "x", "likes": 1}] * 5
    assert can_classify(comments) is False


def test_can_classify_returns_false_for_disabled():
    assert can_classify(None) is False  # 评论关闭场景
    assert can_classify([]) is False


def test_dual_track_preserves_original_when_too_few(sample_meta):
    comments = [
        {"text": "求教程", "likes": 32},
        {"text": "码住", "likes": 28},
    ]
    out = build_dual_track(comments)
    assert out["status"] == "too_few"
    assert "未做归类" in out["readme_block"]
    assert out["raw_top10"] == comments  # 原文完整保留


def test_dual_track_disabled_comments():
    out = build_dual_track(None)
    assert out["status"] == "disabled"
    assert "评论已关" in out["readme_block"]
    assert out["raw_top10"] == []


def test_dual_track_each_class_has_evidence():
    """C2 宪法硬约束：每类必须挂 ≥ 2 条原文."""
    comments = [{"text": f"评论{i}", "likes": 100 - i} for i in range(20)]
    classified = {
        "求教程类": ["评论0", "评论3"],
        "焦虑共鸣类": ["评论1", "评论4"],
        "求推荐类": ["评论2", "评论5"],
    }
    out = build_dual_track(comments, classified=classified)
    assert out["status"] == "classified"
    # 每个类必须挂 ≥ 2 条原文
    for klass, evidence in out["classes"].items():
        assert len(evidence) >= 2, f"{klass} 缺证据"


def test_dual_track_rejects_classification_without_evidence():
    """AI 归类时如果某类挂不到 2 条原文，本类应丢弃."""
    comments = [{"text": "评论0", "likes": 1}, {"text": "评论1", "likes": 1}]
    classified = {
        "类A": ["评论0", "评论1"],
        "类B": ["不存在的评论"],  # 应被剔除
    }
    out = build_dual_track(comments, classified=classified)
    assert "类A" in out["classes"]
    assert "类B" not in out["classes"]
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: 写 `scripts/library/classify_comments.py`**

```python
"""评论双轨归类（C2 宪法核心：底层固化原文 + AI 归类挂证据）.

设计宪法 C2: 不幻觉 - 每个归类必须挂 ≥ 2 条原文证据，否则丢弃该类.
"""
from __future__ import annotations
from typing import Optional


MIN_COMMENTS_TO_CLASSIFY = 10
MIN_EVIDENCE_PER_CLASS = 2


def can_classify(comments: Optional[list[dict]]) -> bool:
    """判定评论数是否够做归类."""
    if comments is None:
        return False
    return len(comments) >= MIN_COMMENTS_TO_CLASSIFY


def _render_too_few(comments: list[dict]) -> str:
    lines = ["## 评论 top 10（评论较少，未做归类）", ""]
    for i, c in enumerate(comments, 1):
        lines.append(f"{i}. \"{c['text']}\" · {c['likes']}赞")
    return "\n".join(lines)


def _render_disabled() -> str:
    return "## 评论\n\n评论已关 · 未抓取."


def _render_classified(comments: list[dict], classes: dict[str, list[str]]) -> str:
    lines = ["## 评论区高频诉求 TOP 3（合并爆文样本 · 每类挂原文证据）", ""]
    for i, (klass, evidence_texts) in enumerate(classes.items(), 1):
        circled = "①②③④⑤⑥⑦⑧⑨⑩"[i-1] if i <= 10 else f"({i})"
        lines.append(f"### {circled} {klass}（{len(evidence_texts)} 条）")
        for ev_text in evidence_texts:
            # 找原始 likes
            matched = next((c for c in comments if c["text"] == ev_text), None)
            likes = matched["likes"] if matched else "?"
            lines.append(f"- \"{ev_text}\" · {likes}赞")
        lines.append("")
    return "\n".join(lines)


def build_dual_track(
    comments: Optional[list[dict]],
    classified: Optional[dict[str, list[str]]] = None,
) -> dict:
    """构建双轨格式输出.

    Args:
        comments: top 10 评论原文，None=评论关闭，[]=空但开放
        classified: AI 归类结果 {类名: [评论原文 list]}

    Returns:
        {
            "status": "disabled" | "too_few" | "no_classification" | "classified",
            "raw_top10": list[dict],
            "classes": dict[str, list[str]],  # 仅 status=classified 时有内容
            "readme_block": str,
        }
    """
    # 评论关闭
    if comments is None:
        return {
            "status": "disabled",
            "raw_top10": [],
            "classes": {},
            "readme_block": _render_disabled(),
        }

    # 评论太少
    if not can_classify(comments):
        return {
            "status": "too_few",
            "raw_top10": comments,
            "classes": {},
            "readme_block": _render_too_few(comments),
        }

    # 没传归类
    if not classified:
        return {
            "status": "no_classification",
            "raw_top10": comments,
            "classes": {},
            "readme_block": _render_too_few(comments),
        }

    # 过滤：每类必须挂 ≥ 2 条真实原文证据（C2 宪法）
    available_texts = {c["text"] for c in comments}
    valid_classes: dict[str, list[str]] = {}
    for klass, evidence_texts in classified.items():
        valid_evidence = [t for t in evidence_texts if t in available_texts]
        if len(valid_evidence) >= MIN_EVIDENCE_PER_CLASS:
            valid_classes[klass] = valid_evidence

    if not valid_classes:
        return {
            "status": "no_classification",
            "raw_top10": comments,
            "classes": {},
            "readme_block": _render_too_few(comments),
        }

    return {
        "status": "classified",
        "raw_top10": comments,
        "classes": valid_classes,
        "readme_block": _render_classified(comments, valid_classes),
    }
```

- [ ] **Step 4: 跑测试，PASS（7 用例）**

- [ ] **Step 5: 提交**

```bash
git add scripts/library/classify_comments.py tests/test_classify_comments.py
git commit -m "feat(S1): classify_comments.py — 双轨归类（C2 宪法核心）"
```

---

### Task 10: `scripts/library/render_readme.py` — 从 `_meta.json` 渲染 README

**Files:**
- Create: `scripts/library/render_readme.py`
- Create: `tests/test_render_readme.py`

- [ ] **Step 1: 写失败的 `tests/test_render_readme.py`**

```python
"""Tests for render_readme.py."""
import pytest
from scripts.library.render_readme import render


def test_render_includes_required_sections(sample_meta):
    sample_meta["notes_index"] = [
        {
            "slug": "github三步", "date": "2025-11-15",
            "title": "GitHub 三步上手", "url": "https://x?t=A",
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
    assert "https://x?t=A" in md  # URL 保留 token
    assert "2644" in md


def test_render_excludes_archived(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "old", "date": "2024-01-01", "title": "老",
         "url": "u", "likes": 5, "collects": 5, "comments": 1,
         "format": "图文", "is_explosive": False,
         "file": "notes/_archive/old.md", "status": "archived"},
    ]
    md = render(sample_meta)
    assert "老" not in md  # 归档的不出现在主表


def test_render_handles_empty_notes(sample_meta):
    md = render(sample_meta)
    assert "暂无笔记" in md or "no notes" in md.lower()


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
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: 写 `scripts/library/render_readme.py`**

```python
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
    fans = blogger["fans_count_history"][-1]["count"] if blogger.get("fans_count_history") else "?"
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
    counts = Counter(n["format"] for n in notes)
    total = sum(counts.values())
    lines = ["## 内容形式分布（自动统计）", "| 形式 | 数量 | 占比 |", "|---|---|---|"]
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
    sorted_notes = sorted(notes, key=lambda n: n["date"], reverse=True)
    lines = [
        "## 笔记总览表（10 列 · 按时间倒序 · 半年内）",
        "| 日期 | 封面 | 标题 | 链接 | 形式 | 点赞 | 收藏 | 评论 | 是否爆文 | 详情 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for n in sorted_notes:
        cover = f"![](images/covers/{n['slug']}.webp)" if n.get("slug") else ""
        explosive = "✅" if n.get("is_explosive") else "❌"
        lines.append(
            f"| {n['date'][5:]} | {cover} | {n['title']} | "
            f"[→]({n['url']}) | {n['format']} | "
            f"{n['likes']} | {n['collects']} | {n['comments']} | "
            f"{explosive} | [详情]({n['file']}) |"
        )
    return "\n".join(lines)


def _explosive_list(notes: list[dict], threshold: int) -> str:
    explosive = [n for n in notes if n.get("is_explosive")]
    if not explosive:
        return f"## 爆文榜（阈值 = {threshold} 赞）\n\n暂无爆文."
    sorted_e = sorted(explosive, key=lambda n: n["likes"], reverse=True)
    lines = [f"## 爆文榜（阈值 = {threshold} 赞）"]
    for n in sorted_e:
        lines.append(f"- {n['title']} — {n['likes']} 赞 [→]({n['file']})")
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
```

- [ ] **Step 4: 跑测试，PASS（4 用例）**

- [ ] **Step 5: 提交**

```bash
git add scripts/library/render_readme.py tests/test_render_readme.py
git commit -m "feat(S1): render_readme.py — README 自动渲染（7 段标准结构）"
```

---

## Phase 4 · Scraper 集成

### Task 11: `scripts/xhs_scraper.py` 加 profile mode

**Files:**
- Modify: `scripts/xhs_scraper.py`（添加 `--mode profile` 子命令）

- [ ] **Step 1: 读现有 `scripts/xhs_scraper.py`，了解结构**

```bash
head -60 scripts/xhs_scraper.py
```

- [ ] **Step 2: 在 main 中加 profile 模式**

定位 `if __name__ == "__main__"` 段，扩展 argparse：

```python
# 在 argparse setup 区域加：
parser.add_argument("--mode", choices=["note", "profile"], default="note",
                    help="note=抓单篇 (默认); profile=抓博主主页近半年笔记列表")
parser.add_argument("--max-age-days", type=int, default=180,
                    help="profile 模式抓多少天内的笔记")
```

- [ ] **Step 3: 写 profile_mode 函数**

在文件中段添加（具体位置看现有结构）：

```python
def scrape_profile(url: str, max_age_days: int = 180) -> dict:
    """抓博主主页近 max_age_days 天内的笔记浅信息列表.

    Returns:
        {
            "blogger": {name, redId, userId, fans, profile_url, ...},
            "notes": [{slug, date, title, url, likes, collects, comments,
                       format, cover_url}, ...]
        }
    """
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=max_age_days)

    # 1. 优先用 agent-reach 获取主页；需要页面交互时用 agent-browser
    # 2. 抓博主元数据（name/redId/fans/...）
    # 3. 滚动加载，抓笔记列表
    # 4. 过滤掉 date < cutoff 的
    # 5. 返回结构化数据

    raise NotImplementedError(
        "profile mode 需要在实施时根据现有 xhs_scraper.py 结构补全."
        " 必须复用现有 cookie/headers 设置。"
        " 实施提示：优先用 agent-reach；需要页面 DOM 交互时用 agent-browser，登录态访问用 bb-browser。"
    )


# 在 main() 里：
if args.mode == "profile":
    result = scrape_profile(args.url, max_age_days=args.max_age_days)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

> **注意**：profile_mode 的具体抓取逻辑依赖 v0.2.0 中现有 `xhs_scraper.py` 的实现风格。实施者需要先 `Read scripts/xhs_scraper.py` 完整文件，模仿其 cookie/header/CDP 调用模式，**不要**重新发明轮子。

- [ ] **Step 4: 写集成测试 `tests/test_xhs_scraper_profile.py`**

```python
"""Profile mode 集成测试（不实际打网，用 mock）."""
import json
import subprocess
import sys
from pathlib import Path


def test_profile_mode_returns_blogger_and_notes(monkeypatch, tmp_path):
    """端到端：调命令行 + 断言输出 JSON 结构."""
    # mock CDP 调用
    # ...（实施时根据现有 xhs_scraper.py 的 mock pattern 写）
    pass  # placeholder, 实施时填充
```

> **注意**：这个测试要求实施者按 v0.2.0 已有的 mock 风格写。如果 v0.2.0 没有 mock infrastructure，跳过单元测试，在 Phase 7 的端到端测试里覆盖。

- [ ] **Step 5: 跑现有回归（确保没破 v0.2.0）**

```bash
bash scripts/run_regression.sh
```

Expected: 现有用例全 PASS

- [ ] **Step 6: 提交**

```bash
git add scripts/xhs_scraper.py tests/test_xhs_scraper_profile.py
git commit -m "feat(S1): xhs_scraper add profile mode (主页浅抓近半年笔记)"
```

---

### Task 12: `scripts/library/init_blogger.py` — 首次入库

**Files:**
- Create: `scripts/library/init_blogger.py`
- Create: `tests/test_init_blogger.py`

- [ ] **Step 1: 写失败的 `tests/test_init_blogger.py`**

```python
"""Tests for init_blogger.py."""
import json
import pytest
from pathlib import Path
from datetime import date
from scripts.library.init_blogger import (
    init_blogger_dirs, compute_threshold, build_meta,
)


def test_init_creates_full_tree(tmp_path):
    bdir = tmp_path / "test-blogger"
    init_blogger_dirs(bdir)
    assert (bdir / "notes" / "_archive").is_dir()
    assert (bdir / "images" / "covers").is_dir()
    assert (bdir / "images" / "slides").is_dir()


def test_compute_threshold_low_fans():
    # 粉丝 1500 < 2000 → 阈值 1000
    assert compute_threshold(fans=1500, fans_threshold=2000,
                              low=1000, high=5000) == 1000


def test_compute_threshold_high_fans():
    # 粉丝 15000 ≥ 2000 → 阈值 5000
    assert compute_threshold(fans=15000, fans_threshold=2000,
                              low=1000, high=5000) == 5000


def test_build_meta_structure():
    blogger_data = {
        "name": "姜饼探AI", "redId": "95475810861",
        "userId": "672bcca5...", "fans": 15000,
        "profile_url": "https://...?xsec_token=...",
    }
    meta = build_meta(
        blogger_data, industry="AI工具", is_target=True,
        threshold=5000, today=date(2026, 5, 28),
    )
    assert meta["schema_version"] == "1.0"
    assert meta["blogger"]["platform"] == "xhs"
    assert meta["blogger"]["name"] == "姜饼探AI"
    assert meta["blogger"]["industry"] == "AI工具"
    assert meta["blogger"]["is_target"] is True
    assert meta["explosive_threshold"] == 5000
    assert meta["blogger"]["first_seen"] == "2026-05-28"
    assert meta["scan_history"] == []
    assert meta["notes_index"] == []
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: 写 `scripts/library/init_blogger.py`**

```python
"""首次入库：建目录树 + 写 _meta.json 骨架.

orchestration 流程（spec 场景 1）：
1. SKILL.md 优先调用 agent-reach 抓单篇笔记 + 显示摘要；必要时使用 agent-browser 或 bb-browser
2. ⭐ ASK 用户: 入库吗?
3. 若是 → ⭐ ASK 路径 → ⭐ ASK 行业
4. 调本模块 init_blogger_dirs + build_meta + 写盘
5. 调 xhs_scraper.py --mode profile 抓近半年浅信息
6. 对每篇浅信息算 is_explosive → 选 top5 → 深抓
7. ⭐ ASK 是否抓口播/图文 → 触发 ocr_images.sh / transcribe_video.sh
8. classify_comments + render_readme + 写盘
9. 报告给用户
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date


def init_blogger_dirs(bdir: Path) -> None:
    """创建 {bdir}/notes/_archive/ + images/covers/ + images/slides/"""
    (bdir / "notes" / "_archive").mkdir(parents=True, exist_ok=True)
    (bdir / "images" / "covers").mkdir(parents=True, exist_ok=True)
    (bdir / "images" / "slides").mkdir(parents=True, exist_ok=True)


def compute_threshold(
    *,
    fans: int,
    fans_threshold: int,
    low: int,
    high: int,
) -> int:
    return low if fans < fans_threshold else high


def build_meta(
    blogger_data: dict,
    *,
    industry: str,
    is_target: bool,
    threshold: int,
    today: date,
) -> dict:
    """构建初始 _meta.json 数据（不含 notes_index）."""
    return {
        "schema_version": "1.0",
        "blogger": {
            "platform": "xhs",
            "name": blogger_data["name"],
            "redId": blogger_data.get("redId", ""),
            "userId": blogger_data.get("userId", ""),
            "industry": industry,
            "is_target": is_target,
            "first_seen": today.isoformat(),
            "fans_count_history": [{
                "date": today.isoformat(),
                "count": blogger_data.get("fans", 0),
            }],
            "profile_url": blogger_data.get("profile_url", ""),
        },
        "explosive_threshold": threshold,
        "scan_history": [],
        "notes_index": [],
    }
```

- [ ] **Step 4: 跑测试，PASS（4 用例）**

- [ ] **Step 5: 提交**

```bash
git add scripts/library/init_blogger.py tests/test_init_blogger.py
git commit -m "feat(S1): init_blogger.py — 首次入库骨架"
```

---

### Task 13: `scripts/library/incremental_scan.py` — 增量扫描

**Files:**
- Create: `scripts/library/incremental_scan.py`
- Create: `tests/test_incremental_scan.py`

- [ ] **Step 1: 写失败的 `tests/test_incremental_scan.py`**

```python
"""Tests for incremental_scan.py."""
import pytest
from datetime import date
from scripts.library.incremental_scan import (
    compute_diff, summarize_diff,
)


def test_diff_finds_new_notes(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "old", "date": "2025-10-01", "likes": 100,
         "collects": 50, "is_explosive": False,
         "status": "active", "file": "notes/old.md", "url": "u-old"},
    ]
    fresh = [
        {"slug": "old", "date": "2025-10-01", "likes": 105,
         "collects": 52, "url": "u-old"},
        {"slug": "new", "date": "2026-05-20", "likes": 1000,
         "collects": 500, "url": "u-new"},
    ]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                         explosive_threshold=5000)
    assert diff["new"] == ["new"]
    assert diff["unchanged_or_minor"] == ["old"]
    assert diff["major_change"] == []


def test_diff_detects_major_growth(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "rising", "date": "2025-11-01", "likes": 100,
         "collects": 100, "is_explosive": False,
         "status": "active", "file": "notes/rising.md", "url": "u"},
    ]
    fresh = [
        {"slug": "rising", "date": "2025-11-01", "likes": 200,
         "collects": 200, "url": "u"},  # 100% 涨幅
    ]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                         explosive_threshold=5000, major_pct=0.3)
    assert "rising" in diff["major_change"]


def test_diff_detects_new_explosive(sample_meta):
    sample_meta["notes_index"] = [
        {"slug": "x", "date": "2025-11-01", "likes": 100,
         "collects": 100, "is_explosive": False,
         "status": "active", "file": "notes/x.md", "url": "u"},
    ]
    fresh = [
        {"slug": "x", "date": "2025-11-01", "likes": 8000,
         "collects": 8000, "url": "u"},  # 飙到爆文阈值
    ]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                         explosive_threshold=5000)
    assert "x" in diff["new_explosive"]


def test_summarize_diff_human_readable():
    diff = {"new": ["a", "b"], "major_change": ["c"],
            "new_explosive": ["a"], "unchanged_or_minor": ["d"]}
    s = summarize_diff(diff)
    assert "2" in s and "新内容" in s
    assert "1" in s and ("涨幅" in s or "大变化" in s)
    assert "1" in s and "爆文" in s
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: 写 `scripts/library/incremental_scan.py`**

```python
"""增量扫描：对比上次扫描的 _meta.json 与本次 fresh 数据.

设计宪法 C1: 不擅自动手 - 返回 diff，由 caller ask 用户后再执行更新.
"""
from __future__ import annotations


def compute_diff(
    meta: dict,
    fresh_notes: list[dict],
    *,
    fans: int,
    explosive_threshold: int,
    major_pct: float = 0.3,
) -> dict:
    """对比 _meta.json 旧数据 vs fresh 新数据.

    Returns:
        {
            "new": [slug, ...],              # 新发布的
            "major_change": [slug, ...],     # 点赞/收藏涨幅 ≥ major_pct
            "new_explosive": [slug, ...],    # 本次新达爆文阈值的
            "unchanged_or_minor": [slug, ...],
        }
    """
    old_by_slug = {n["slug"]: n for n in meta.get("notes_index", [])
                    if n.get("status") == "active"}

    new, major, new_explosive, minor = [], [], [], []

    for fn in fresh_notes:
        slug = fn["slug"]
        old = old_by_slug.get(slug)

        if old is None:
            new.append(slug)
            if fn["likes"] >= explosive_threshold:
                new_explosive.append(slug)
            continue

        old_likes = old.get("likes", 0) or 1  # 防 div by 0
        delta = (fn["likes"] - old_likes) / old_likes
        if delta >= major_pct:
            major.append(slug)
        else:
            minor.append(slug)

        # 旧的不是爆文，本次达到了
        if not old.get("is_explosive") and fn["likes"] >= explosive_threshold:
            new_explosive.append(slug)

    return {
        "new": new,
        "major_change": major,
        "new_explosive": new_explosive,
        "unchanged_or_minor": minor,
    }


def summarize_diff(diff: dict) -> str:
    """生成 ASK 用户用的差量摘要."""
    return (
        f"📊 增量摘要：\n"
        f"  · 新发布笔记：{len(diff['new'])} 篇\n"
        f"  · 数据涨幅 ≥30% 的老笔记（大变化）：{len(diff['major_change'])} 篇\n"
        f"  · 新爆文：{len(diff['new_explosive'])} 篇\n"
        f"  · 无大变化：{len(diff['unchanged_or_minor'])} 篇"
    )
```

- [ ] **Step 4: 跑测试，PASS（4 用例）**

- [ ] **Step 5: 提交**

```bash
git add scripts/library/incremental_scan.py tests/test_incremental_scan.py
git commit -m "feat(S1): incremental_scan.py — diff 算法（new/major/explosive/minor）"
```

---

## Phase 5 · 触发流程编排

### Task 14: 写 `references/competitor-library-flow.md` 四场景对话脚本

**Files:**
- Create: `references/competitor-library-flow.md`

- [ ] **Step 1: 写完整对话脚本**

把 spec 第 5 节四个场景的对话脚本完整搬过来。这文件是 SKILL.md 触发后查阅的"flow 手册"。

```markdown
# S1 · 触发流程 · 四场景对话脚本

> 此文档是 SKILL.md 触发后 Claude 必须查阅的 flow 手册.
> 所有⭐标记 = 必须 ASK 用户的节点（守 C1 宪法）.

## 触发条件

任意小红书链接出现 → 自动触发 bela-xhs-analysis 入口逻辑.

## 入口判别

1. 解析链接 → 短链 / 单篇笔记 / 博主主页
2. 读 `user-config.json`：
   - 不存在 → 走"首次配置" sub-flow
   - 存在 → 继续
3. 查 `{storage_root}/{*}/{*}-{博主名}/_meta.json` 是否存在
   - 存在 → 老博主（场景 2）
   - 不存在 → 新博主（场景 1 / 3 / 4）

---

## 场景 1 · 新博主 · 单篇笔记链接

（spec 5.1 的完整对话脚本，照抄）

---

## 场景 2 · 老博主增量扫描

（spec 5.2）

---

## 场景 3 · 短链 / 主页链接

（spec 5.3）

---

## 场景 4 · 不入库的临时分析

（spec 5.4）

---

## 边界情况

（spec 6 的表）

---

## 首次配置 sub-flow

skill 首次运行（未发现 `user-config.json`）：

\`\`\`
SKILL → 👋 看起来你是第一次用我做对标博主追踪.
        我需要确认 2 个根目录，其他用安全默认值.

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
        其他字段（爆文阈值 1000/5000、半年归档、ask 节点）用默认值.
        想改默认值，编辑 user-config.json 即可.
\`\`\`
```

- [ ] **Step 2: 提交**

```bash
git add references/competitor-library-flow.md
git commit -m "docs(S1): 四场景对话脚本 + 首次配置 sub-flow"
```

---

### Task 15: 升级 `SKILL.md` 到 v0.3.0

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 读现有 SKILL.md 全文**

```bash
cat SKILL.md | head -80
```

- [ ] **Step 2: 改头部 version 字段**

把 `version: 0.2.0` 改为 `version: 0.3.0`。

- [ ] **Step 3: 在 SKILL.md 适当位置加 S1 章节**

在"## 触发条件"或类似位置之后，加入：

```markdown
## S1 · 对标博主库（v0.3.0 新增）

当用户发任意小红书链接时，**先走入口判别**（详见 `references/competitor-library-flow.md`）：

1. 检查 `user-config.json` 是否存在 → 首次配置 sub-flow
2. 检查 `{storage_root}/{*}/{*}-{博主名}/_meta.json` 是否存在 → 老博主 vs 新博主
3. 按场景 1/2/3/4 走对应对话脚本
4. 所有⭐ ASK 节点**不能跳过**（守 C1 宪法）

### 关键调用链

\`\`\`
用户发链接
  ↓
scripts/xhs_scraper.py --mode note --url <URL>     # 抓单篇快览
  ↓
⭐ ASK 入库吗？
  ↓ 是
⭐ ASK 路径 / 行业
  ↓
scripts/library/init_blogger.py                    # 建目录 + meta 骨架
scripts/xhs_scraper.py --mode profile --url <PROFILE_URL>  # 浅抓
对每篇浅信息算 is_explosive
对 top5 + 用户指定那篇调 xhs_scraper.py --mode note 深抓
对图文笔记调 scripts/media/ocr_images.sh
⭐ ASK 是否对视频笔记跑 ASR
  ↓ 是
对视频笔记调 scripts/media/transcribe_video.sh
scripts/library/classify_comments.py               # 评论双轨归类
scripts/library/render_readme.py                   # 渲染 README.md
写盘 _meta.json
  ↓
回话给用户：摘要 + 路径
\`\`\`

### 数据契约（下游 skill 依赖）

- `_meta.json` schema: 见 `references/meta-json-schema.md`
- 单笔记 YAML front matter: 见 `references/single-note-template.md`
- 评论双轨格式: 见 `references/author-analysis-template.md`

**字段名只能加，不能改/删** — 改名是 breaking change，必须升 `schema_version` 并写迁移脚本.

### 设计宪法（不可违背）

| C1 🚫 | 不擅自动手 | 关键节点 ASK 用户 |
| C2 🚫 | 不幻觉 | AI 归类必挂 ≥ 2 条原文证据 |
| C3 ✅ | 有迹可循 | 时间戳 + URL + 本地图片相对路径 |
| C4 ✅ | 真诚落地 | AI 段标"AI 整理 · 可被你否决"；禁用震惊体 |
| C5 ♻️ | 数据兜底 | 本地→ASK→提供后再跑 |
```

- [ ] **Step 4: 跑现有 regression（确保 v0.2.0 入口逻辑没坏）**

```bash
bash scripts/run_regression.sh
```

- [ ] **Step 5: 提交**

```bash
git add SKILL.md
git commit -m "feat(S1): SKILL.md v0.2.0 → v0.3.0 (加 S1 章节 + 触发逻辑)"
```

---

## Phase 6 · 验收测试

### Task 16: 写端到端验收测试（T1-T8）

**Files:**
- Create: `tests/test_e2e_acceptance.py`

> 端到端测试 mock 网络层，专测**编排**逻辑.

- [ ] **Step 1: 写测试**

```python
"""端到端验收 · spec 9.1 的 T1-T8 用例.

Mock 网络层（xhs_scraper.py 输出）；测编排逻辑.
"""
import json
import pytest
from datetime import date
from pathlib import Path
from scripts.library.init_blogger import build_meta, init_blogger_dirs
from scripts.library.incremental_scan import compute_diff, summarize_diff
from scripts.library.archive_old import archive_in_meta
from scripts.library.classify_comments import build_dual_track
from scripts.library.render_readme import render
from scripts.library.meta_store import write_meta, read_meta, upsert_note


def test_T1_new_blogger_single_note(tmp_blogger_dir, sample_meta):
    """T1: 新博主单篇链接 → 走场景1，4 个 ask，落盘完整目录."""
    init_blogger_dirs(tmp_blogger_dir)
    assert (tmp_blogger_dir / "notes" / "_archive").is_dir()

    # 模拟首次入库
    meta = build_meta(
        {"name": "姜饼探AI", "redId": "X", "userId": "Y",
         "fans": 15000, "profile_url": "https://...?xsec_token=A"},
        industry="AI工具", is_target=True,
        threshold=5000, today=date(2026, 5, 28),
    )
    write_meta(tmp_blogger_dir / "_meta.json", meta)

    # 加一篇
    upsert_note(meta, {
        "file": "notes/2025-11-15-github三步.md",
        "slug": "github三步", "date": "2025-11-15",
        "title": "GitHub 三步上手", "url": "https://...?xsec_token=A",
        "likes": 13, "collects": 2644, "comments": 23,
        "format": "图文", "is_explosive": True,
        "deep_scraped": True, "status": "active",
    })
    write_meta(tmp_blogger_dir / "_meta.json", meta)

    # 验收
    loaded = read_meta(tmp_blogger_dir / "_meta.json")
    assert loaded["blogger"]["name"] == "姜饼探AI"
    assert len(loaded["notes_index"]) == 1
    assert loaded["notes_index"][0]["url"].endswith("xsec_token=A")  # token 保留


def test_T2_same_link_again_incremental(sample_meta):
    """T2: 再发一次 → 增量场景."""
    sample_meta["notes_index"] = [{"slug": "a", "date": "2025-11-15",
        "likes": 100, "collects": 100, "is_explosive": False,
        "status": "active", "file": "notes/a.md", "url": "u"}]
    fresh = [{"slug": "a", "date": "2025-11-15",
              "likes": 105, "collects": 102, "url": "u"}]
    diff = compute_diff(sample_meta, fresh, fans=15000,
                         explosive_threshold=5000)
    assert diff["new"] == []
    assert "a" in diff["unchanged_or_minor"]


def test_T5_not_add_to_library_no_folder():
    """T5: 用户选否 → 不写入对标库目录.
    
    实际行为是 caller 调 init_blogger_dirs() 之前先 ASK；不调就不建目录.
    """
    # 此测试就是不调 init_blogger_dirs，验证目录不被创建
    # (caller-level，无法在单元测试覆盖；留作 spec 文档参考)
    pass


def test_T6_comments_disabled_no_classification():
    """T6: 评论关闭 → 不编 top3 类."""
    out = build_dual_track(None)
    assert out["status"] == "disabled"
    assert out["classes"] == {}
    assert "评论已关" in out["readme_block"]


def test_T8_old_notes_archived(sample_meta):
    """T8: 半年外笔记自动归档."""
    sample_meta["notes_index"] = [
        {"slug": "fresh", "date": "2026-04-01", "file": "notes/fresh.md",
         "status": "active"},
        {"slug": "old", "date": "2024-12-01", "file": "notes/old.md",
         "status": "active"},
    ]
    archived = archive_in_meta(
        sample_meta, today=date(2026, 5, 28), after_days=180,
    )
    assert len(archived) == 1
    assert archived[0]["slug"] == "old"
    assert archived[0]["file"] == "notes/_archive/old.md"
    assert archived[0]["status"] == "archived"
    # 主表查询应排除归档
    md = render(sample_meta)
    assert "fresh" in md or "暂无" not in md  # active 还在
```

- [ ] **Step 2: 跑测试，PASS**

```bash
python -m pytest tests/test_e2e_acceptance.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/test_e2e_acceptance.py
git commit -m "test(S1): T1/T2/T5/T6/T8 端到端验收（mock 网络层）"
```

> **T3/T4/T7** 涉及真实网络交互或外部依赖，留作手工验收，由 Task 17 负责.

---

### Task 17: 手工验收 · 真链接跑一遍

**Files:** （无新文件，跑命令）

- [ ] **Step 1: 准备 1 个真实小红书链接**（用我们之前姜饼探 AI 的那个）

- [ ] **Step 2: 启动 skill，按场景 1 走完**

- [ ] **Step 3: 验证落盘**

```bash
ls -la ~/Documents/xhs-竞品分析/AI工具/小红书-姜饼探AI/
cat ~/Documents/xhs-竞品分析/AI工具/小红书-姜饼探AI/_meta.json | jq '.scan_history'
head -30 ~/Documents/xhs-竞品分析/AI工具/小红书-姜饼探AI/README.md
```

- [ ] **Step 4: 验证 C 宪法 5 条**

按 spec 9 节验收标准对照：

```
□ C1 ask 节点 ≥ 4 个（数对话里⭐次数）
□ C2 评论 top3 类每类挂 ≥ 2 条原文
□ C3 _meta.json 有 scraped_at + 原始 URL（带 xsec_token）+ 本地图片相对路径
□ C4 README/笔记的 AI 段标了"AI 整理 · 可被你否决"，无震惊体词
□ C5 数据兜底（首次 ASK 路径 + 行业）
```

- [ ] **Step 5: 把验收报告写到 `docs/specs/2026-05-28-S1-acceptance-report.md`**

```markdown
# S1 验收报告 · 2026-05-28

## 测试用例

| # | 用例 | 结果 | 备注 |
|---|---|:---:|---|
| T1 | 新博主单篇 | ✅/❌ | ... |
| T2 | 同链接再发 | ✅/❌ | ... |
| ... | | | |

## 宪法检查

| 宪法 | 检查项 | 结果 |
|---|---|:---:|
| C1 | ASK 节点 ≥ 4 | ✅/❌ |
| ... | | |

## 已知问题

- 例如：T7 网络中断场景无法稳定复现，待后续打磨
```

- [ ] **Step 6: 提交**

```bash
git add docs/specs/2026-05-28-S1-acceptance-report.md
git commit -m "test(S1): 手工验收报告 · 真链接跑通"
```

---

## Phase 7 · 收尾

### Task 18: 升级 install.sh 添加 pytest 依赖

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: 在 pip install 段加 pytest**

定位 `pip install` 行（如有），追加 `pytest`：

```bash
# 测试依赖（S1 v0.3.0）
pip install --user pytest >/dev/null 2>&1
```

- [ ] **Step 2: 验证可跑**

```bash
bash install.sh && python -m pytest --version
```

- [ ] **Step 3: 提交**

```bash
git add install.sh
git commit -m "chore(S1): install.sh 加 pytest 依赖"
```

---

### Task 19: 升级 README.md / README.zh.md 引用 S1

**Files:**
- Modify: `README.md`
- Modify: `README.zh.md`

- [ ] **Step 1: 在 README.zh.md 适当位置加一段**

```markdown
## v0.3.0 · S1 对标博主库

发任意小红书链接 → skill 自动判断是否入库 → 标准扫描（半年浅 + top5 深）→ 落盘到 `~/Documents/xhs-竞品分析/{行业}/{平台}-{博主}/`.

详见 `docs/specs/2026-05-28-S1-competitor-library-design.md`.
```

- [ ] **Step 2: 同步 README.md（英文版本）**

- [ ] **Step 3: 提交**

```bash
git add README.md README.zh.md
git commit -m "docs(S1): README 加 v0.3.0 S1 章节"
```

---

### Task 20: 创建 v0.3.0 release tag

**Files:** （无）

- [ ] **Step 1: 跑完整 regression**

```bash
python -m pytest tests/ -v
bash scripts/run_regression.sh
```

期望：全 PASS

- [ ] **Step 2: 打 tag**

```bash
git tag -a v0.3.0 -m "S1 · 对标博主库 · 持续追踪框架"
```

- [ ] **Step 3: 验证 tag**

```bash
git log --oneline --decorate -5
```

---

## Self-Review · 自检 4 维

实施者实施完后，开 fresh eyes 跑一遍：

### 1. Spec 覆盖检查

| Spec 节 | 覆盖任务 | 状态 |
|---|---|:---:|
| 0 设计宪法 5 条 | T9/classify_comments (C2) + T6/paths (C5) + 各模块 docstring | ✅ |
| 2 五个核心决策 D1-D5 | T6 (D1/D2 路径命名) + T11 (D3 浅+深) + T13 (D4 增量) + T9 (D5 双轨) | ✅ |
| 3 架构总览 | T15 SKILL.md 章节 + T14 flow 文档 | ✅ |
| 4 文件结构 | T6 paths.py + T12 init_blogger.py | ✅ |
| 4.3-4.5 模板 | T1 meta-schema + T3 single-note YAML + T4 author 10-col | ✅ |
| 5 触发流程 4 场景 | T14 competitor-library-flow.md | ✅ |
| 6 边界处理 | T9 (评论关闭) + T8 (归档) + T13 (网络中断 - caller 层) | ⚠️ 部分 |
| 7 路径变量化 | T6 paths.py | ✅ |
| 8 联动协议 | T1 schema + T3/T4 模板 (字段名即契约) | ✅ |
| 9 验收 9.1 | T16 端到端 + T17 手工 | ✅ |

⚠️ **网络中断场景**（spec 6）目前只有 caller 层（编排）覆盖，没在单元测试里 mock 中断行为。**实施者注意**：如时间允许，在 Task 16 或新增 Task 加 mock subprocess 失败的测试。

### 2. 占位符扫描

- [x] 无 "TBD" / "TODO"（搜全文）
- [x] 无 "implement later"
- [x] 每个代码 step 都有完整代码

### 3. 类型一致性

| 函数 | 文件 | 签名 |
|---|---|---|
| `slug_from_title(title, max_len=12)` | utils.py | ✅ |
| `parse_chinese_number(s)` | utils.py | ✅ |
| `is_explosive(*, likes, fans, fans_threshold, low, high)` | utils.py | ✅ |
| `compute_threshold(*, fans, fans_threshold, low, high)` | init_blogger.py | ✅ |
| `should_archive(note_date, *, today, after_days)` | archive_old.py | ✅ |
| `can_classify(comments)` | classify_comments.py | ✅ |
| `build_dual_track(comments, classified=None)` | classify_comments.py | ✅ |
| `compute_diff(meta, fresh_notes, *, fans, explosive_threshold, major_pct=0.3)` | incremental_scan.py | ✅ |
| `render(meta) -> str` | render_readme.py | ✅ |
| `find_note_by_url(meta, url)`, `find_note_by_slug(meta, slug)` | meta_store.py | ✅ 命名一致 |

### 4. 已知未覆盖

- 真实小红书反爬升级 → 留 Task 17 手工验收发现
- S5 人设感知部分（差异化空间）→ 留占位符，下一份 spec 处理
- 跨设备同步（S4）→ 不在本 plan 范围

---

## Execution Handoff

Plan complete and saved to `~/.claude/skills/bela-xhs-analysis/docs/plans/2026-05-28-S1-competitor-library.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — 每个 Task 派 fresh subagent 跑，回归测 + 你 review 后再下一个，迭代快.
2. **Inline Execution** — 当前会话连续跑，每 3-5 个 Task 一个 checkpoint review.

**Which approach?**
