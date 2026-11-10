# user-config.json · 首次使用引导

skill 首次运行时检查 `~/.claude/skills/bela-xhs-analysis/user-config.json` 是否存在：

- **不存在** → 只 ASK 2 个最关键值：
  1. `storage_root`（对标库根目录，默认 `~/Documents/xhs-竞品分析`）
  2. `persona_root`（用户人设档案目录，默认 `~/Documents/个人档案`）

  其他字段自动用安全默认值（见 `user-config.json.example`）。

- **存在** → 直接读取，不重复问。

---

## 字段说明

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `schema_version` | string | `"1.0"` | 升级时迁移用 |
| `storage_root` | path | `~/Documents/xhs-竞品分析` | 对标库根目录 |
| `persona_root` | path | `~/Documents/个人档案` | S5 用户人设档案 |
| `default_industry` | string\|null | `null` | **永远 null，每次都问**（守 C1 宪法） |
| `explosive_threshold_low` | number | `1000` | 粉丝 < `fans_threshold` 时的爆文阈值 |
| `explosive_threshold_high` | number | `5000` | 粉丝 ≥ `fans_threshold` 时的爆文阈值 |
| `fans_threshold` | number | `2000` | 粉丝量分档 |
| `archive_after_days` | number | `180` | 半年外归档（不删除，进 `_archive/`） |
| `scan_depth_default` | string | `"standard"` | `"minimal"` / `"standard"` / `"full"` |
| `ask_on_each_scan` | boolean | `true` | 每次扫描前是否 ASK（守 C1 宪法） |

---

## 路径变量

文件中所有路径支持：
- `~` 展开为 `$HOME`（实现于 `scripts/library/paths.py:storage_root()`）
- **不展开环境变量**（避免 leak）

---

## 跨设备 / 跨用户共享

`user-config.json` 含本地路径，**已加入 `.gitignore`**。如需共享，参考 `user-config.json.example` 在新机器手动建一份。

未来 S4（跨设备同步）会自动处理 config 迁移。

---

## 设计宪法守门

| 字段 | 对应宪法 |
|---|---|
| `default_industry: null` | C1（不擅自动手）—— 每次都问 |
| `ask_on_each_scan: true` | C1 |
| `archive_after_days` | C3（有迹可循）—— 归档不删除 |
| `explosive_threshold_*` | C2（不幻觉）—— 阈值显式可配，不靠 AI 猜 |

---

## 修改 config 后

直接编辑 `user-config.json` 即可。skill 每次启动重新读取，无需重启 Claude Code。

如改了 `storage_root` 想搬已有数据，**自己 `mv` 文件夹**（或等 S4 提供迁移命令）——skill 当前不会自动搬移。
