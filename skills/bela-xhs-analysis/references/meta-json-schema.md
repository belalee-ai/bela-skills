# _meta.json Schema · v1.0

每个博主目录下都有一份 `_meta.json`，是程序化元数据的**唯一来源**。

**契约稳定性**：字段名 = 下游 skill（S2/S3/S5/S4）写死的依赖，**只能增不能改**。改字段名必须升 `schema_version` 并提供迁移脚本。

---

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `schema_version` | string | ✅ | 当前 `"1.0"`；breaking change 时升级 |
| `blogger` | object | ✅ | 博主元数据 |
| `explosive_threshold` | number | ✅ | 当前粉丝量对应的爆文阈值（粉丝 < `fans_threshold` → `low`，≥ → `high`） |
| `scan_history` | array | ✅ | 每次扫描的时间 + 摘要 |
| `notes_index` | array | ✅ | 所有笔记的索引（含归档） |

---

## `blogger` 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `platform` | string | ✅ | 固定 `"xhs"`；预留多平台 |
| `name` | string | ✅ | 博主昵称 |
| `redId` | string | ✅ | 小红书号；歧义消解的唯一键 |
| `userId` | string | ✅ | URL 中的 `user/profile/{userId}` |
| `industry` | string | ✅ | 用户分类（如 `"AI工具"` / `"营养师"` / `"职场"`） |
| `is_target` | boolean | ✅ | 是否对标账户（用户首次入库时确认） |
| `first_seen` | string | ✅ | 首次入库日期 `YYYY-MM-DD` |
| `fans_count_history` | array | ✅ | 粉丝量历史，元素 `{date, count}` |
| `profile_url` | string | ✅ | 主页 URL（带 `xsec_token`） |

---

## `scan_history` 元素字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `date` | string | ISO 8601 timestamp（含时区） |
| `notes_scanned` | number | 浅抓笔记数 |
| `notes_deep` | number | 深抓笔记数 |
| `new_explosive` | number | 本次新增爆文数 |

---

## `notes_index` 元素字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `file` | string | 相对路径 `notes/{slug}.md` 或 `notes/_archive/{slug}.md` |
| `slug` | string | 笔记 slug，对应文件名 |
| `date` | string | 笔记发布日期 `YYYY-MM-DD` |
| `title` | string | 笔记标题（原文） |
| `url` | string | 完整 URL（含 `xsec_token`） |
| `likes` | number | 点赞数 |
| `collects` | number | 收藏数 |
| `comments` | number | 评论总数 |
| `format` | string | `"图文"` / `"视频"` |
| `is_explosive` | boolean | 按当前 `explosive_threshold` 算 |
| `last_updated` | string | ISO 8601 timestamp（含时区） |
| `deep_scraped` | boolean | 是否做过深抓（正文 OCR + 评论 top10） |
| `asr_extracted` | boolean | 视频笔记是否做过 ASR |
| `comments_disabled` | boolean | 评论是否被博主关闭 |
| `top_comments_path` | string | 形如 `notes/{slug}.md#评论-top-10` 的锚点 |
| `status` | string | `"active"` / `"archived"` / `"deleted"` |

---

## 完整示例

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
    "profile_url": "https://www.xiaohongshu.com/user/profile/672bcca5000000001c01bfed?xsec_token=ABxCUbc4UF4v9sy0U0yz2FO1EKuLVnBxqP5YJ3yWNaO8U="
  },
  "explosive_threshold": 5000,
  "scan_history": [
    {
      "date": "2026-05-28T14:30:00+08:00",
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
      "title": "普通人学AI必看，GitHub三步上手",
      "url": "https://www.xiaohongshu.com/discovery/item/69f49c9e000000003501df28?xsec_token=ABUsD6H5v_em7yypNzueZ5zV7SnIEkNgJDPfh-b3qhuxk=",
      "likes": 13,
      "collects": 2644,
      "comments": 23,
      "format": "图文",
      "is_explosive": true,
      "last_updated": "2026-05-28T14:30:00+08:00",
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

## 字段使用约定

### URL 归一化

匹配两条 `url` 是否同一篇笔记时，**剥离会过期的参数**：
- `xsec_token`
- `share_id`
- `shareRedId`
- `apptime`

保留 `?` 前的协议 + host + path 作为唯一标识。具体实现见 `scripts/library/meta_store.py:_strip_xsec()`。

### 时间戳

所有 ISO 8601 时间戳带 `+08:00` 时区。生成用 `scripts/library/utils.py:iso_now()`。

### slug 规则

见 `scripts/library/utils.py:slug_from_title()`：
- 取标题前 12 个有效字符（汉字 / 字母 / 数字 / `-` / `_`）
- 去空格、标点、emoji、`#` 话题符号
- 撞名追加 `-2` `-3`

### 爆文阈值动态计算

- 粉丝 < `fans_threshold` → 阈值 = `explosive_threshold_low`（默认 1000）
- 粉丝 ≥ `fans_threshold` → 阈值 = `explosive_threshold_high`（默认 5000）
- 每次扫描时基于**当时的粉丝量**重算 `explosive_threshold` 并写入 meta

---

## 下游 skill 依赖矩阵

| skill | 读哪些字段 |
|---|---|
| S2（正文/口播抓取） | `notes_index[].file` / `.deep_scraped` / `.asr_extracted` |
| S3（多格式产出） | `notes_index[].file` / `.title` / `.url` / `.format` |
| S5（人设感知生产） | `notes_index[].is_explosive` / `.likes` + `blogger.industry` |
| S4（跨设备同步） | 整目录结构（不读字段） |

**任何字段重命名都是 breaking change**，必须：
1. `schema_version` 升级（`1.0` → `1.1` / `2.0`）
2. 提供迁移脚本 `scripts/library/migrate_meta.py`
3. 通知所有下游 skill 适配
