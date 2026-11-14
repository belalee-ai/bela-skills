---
name: bela-tiny-png
description: 调用 TinyPNG 官方 API 对【已存在于本地文件夹的位图】做批量后处理 —— 压缩、缩放、转 WebP/AVIF/JPEG/PNG、生成社交平台尺寸（小红书 / 微信 / 朋友圈 / IG / Twitter/X / 微博 / 抖音 等 16 种）、保留 EXIF。自动支持 iPhone HEIC、并发处理、智能缓存跳过重复调用、原图自动备份、超过 Tinify API 单文件上限时自动跳过。**该用此技能的信号**：用户提到 tinypng / 压缩图片 / 批量压缩 / 缩小图片 / 瘦身 / 减肥 / 压一下 iPhone 照片 / 批量处理 HEIC / 缩到 XXX 像素 / 转 WebP / 转 AVIF / 做小红书图 / 做公众号封面 / 做朋友圈 / IG / Twitter/X / 微博 / 抖音 / 生成多尺寸 / 生成全平台 / 批量裁切 / 缩略图 / 给图片换格式 / 调整图片尺寸 / 批量优化某文件夹的照片 / 批量处理客片 / 处理摄影成片。**不该用此技能的信号**：用户要 AI 修图（去水印、去人物、抠图、人脸美化）、矢量图编辑（SVG/AI/PDF）、RAW 解码（CR2/NEF/ARW）、GIF/视频处理、单张图片在线分享 —— 这些都不在 TinyPNG 能力范围。Use this skill for batch local-folder image post-processing via TinyPNG (compress / resize / convert WebP, AVIF / social media presets / preserve metadata / iPhone HEIC), NOT for AI editing, vector graphics, RAW decoding, or video.
---

# bela-tiny-png 图片批量处理

从本地技能 `ameng-tiny-png` 迁入。使用 [TinyPNG 官方 API](https://tinypng.com/developers) 处理图片，运行时会上传待处理的图片。

## TL;DR（30 秒上手）

**做什么**：调 TinyPNG API，对本地文件夹里的位图做"压缩 + 缩放 + 转格式 + 留元数据"。

**入口**：`python3 "<SKILL_DIR>/scripts/compress.py" "<用户文件夹>" [选项]`

**核心心法 5 步**：
1. **前置检查**：装依赖 + 验 API key（缺哪个就引导哪个）
2. **理解需求**：把用户话翻译成"是否覆盖 / 用什么预设 / 转什么格式 / 保留什么"
3. **估算配额**：算 `图片数 × 预设数 × 格式数`，超阈值停下问用户
4. **执行**：直接跑（含 `--dry-run` 选项）
5. **展示**：原样贴脚本输出的表格 + 一句话收尾 + 提示下一步

⚠️ **TinyPNG 是有损压缩。第一次为某用户处理时主动建议先备份或用 `--backup`。**

---

## 边界（什么时候说"我不做"）

如果用户其实想要下面这些，**不要用本 skill**，直接说明并建议替代方案：

| 用户想做 | 不在 skill 范围 | 建议方向 |
|---------|---------------|---------|
| AI 修图（去水印 / 去物体 / 美颜 / 抠图）| TinyPNG 不会改像素内容 | 用 Photoshop / 美图秀秀 / 在线 AI 工具 |
| 矢量图编辑（SVG / AI / PDF）| 仅处理位图 | 用 Illustrator / Inkscape |
| RAW 解码（CR2 / NEF / ARW / DNG）| TinyPNG 不收 RAW | 先用 Lightroom / Capture One 导出 JPEG/HEIC |
| GIF 动图 / 视频 | 仅静图 | 用 ffmpeg / Handbrake |
| 单张图片在线分享 / 转链接 | 仅本地处理 | 用图床（七牛 / SM.MS / Imgur） |
| 加水印 / 加文字 | TinyPNG 不做合成 | 用 ImageMagick / 美图秀秀 |

如果用户上传的**只是单张图片**且没说"批量"，先确认意图：是要批量处理一个文件夹，还是只想知道某个工具？

---

## 能力地图（按场景分组）

### 📦 体积优化场景
- "压缩" "瘦身" "减肥" "缩小体积" → 默认调用即可
- "转 WebP" "转 AVIF" "换 JPEG" → `--convert <格式>`

### 📐 尺寸调整场景
- "缩到 1080 宽" "等比缩" → `--resize-method scale --width N`
- "1:1 1080" "智能裁切" → `--resize-method cover --width 1080 --height 1080`
- "300×300 缩略图 / 头像" → `--resize-method thumb --width 300 --height 300`

### 📱 社交媒体场景
- "做小红书图" → `--preset xiaohongshu`
- "做公众号封面" → `--preset wechat-cover`
- "朋友圈" → `--preset moments`
- "IG 方图 / Story" → `--preset instagram-square` / `instagram-story`
- "Twitter 推文 / 头图" → `--preset twitter-post` / `twitter-header`
- "抖音" → `--preset douyin`
- "全平台一键" → `--multi-size all-social`
- 其它 bundle 见 [Step 5 速查表](#step-5-命令速查表) 或 `--list-presets`

### 📷 摄影后期场景
- "iPhone 照片" "HEIC" → 自动检测，无需特殊参数（需 pillow-heif）
- "保留拍摄时间" → `--preserve creation`
- "保留 GPS" → `--preserve location`

### 🛡️ 安全 / 性能场景
- "覆盖原图但留底" → `--backup`
- "已经做过的不要重做" → `--no-overwrite`
- "跳过 thumb 文件" → `--exclude "*.thumb.*"`
- "强制重做（忽略缓存）" → `--force`
- "更快 / 更慢" → `--workers N`（默认 4，1=串行，最多 16）

### 🔧 工具命令
- 看预设 → `--list-presets`
- 看配置（key + 缓存 + HEIC 状态）→ `--show-config`
- 切换账号 → `--unset-api-key` 然后 `--set-api-key NEW`
- 预演不调 API → 任何命令加 `--dry-run`

---

## 智能行为（无需用户操心，但 Claude 要知道）

| 行为 | 触发时机 | 影响 |
|------|---------|------|
| 🔄 缓存自动跳过 | 默认开启 | 同文件 + 同操作命中缓存 → 不耗 API |
| 📷 HEIC 自动转 JPEG | 检测到 .heic/.heif | 需 `pillow-heif`，缺则跳过并提示 |
| 📦 超过 API 上限自动跳过 | 文件超过 Tinify API 单文件限制（当前 500MB / 256MP） | 提前列出并跳过，不浪费 API |
| 🛡️ 覆盖保护 | 用了 resize/preset/multi-size/convert 但没传 `--output` | 自动建 `<源>_xxx` 输出目录 |
| ⚡ 并发处理 | 默认 4 worker | 50 张约 15 秒 |
| 📝 汇总只打印不落盘 | 默认行为 | 结果表格只显示在当前终端流程里 |
| 📝 可选报告文件 | 显式加 `--write-report` | 输出 `_report.md` |
| 📊 配额自动显示 | 执行前 / 后 | 显示 `已用 / 500` |

---

## Step 1：前置检查（合并依赖 + API key）

按这个顺序检查，缺什么就引导补什么：

### 1a. tinify 依赖
```bash
pip install --quiet tinify --break-system-packages
```
（HEIC 用户额外：`pip install --quiet pillow pillow-heif --break-system-packages`）

### 1b. API key
```bash
python3 "<SKILL_DIR>/scripts/compress.py" --check-api-key
```
- **退出码 0**：✅ 已配置，进入 Step 2
- **退出码 4**：未配置，用以下话术引导：

> 🔑 还没找到你的 TinyPNG API key 哦～
>
> 30 秒搞定：
> 1️⃣ 打开 👉 https://tinypng.com/developers
> 2️⃣ 输入姓名 + 邮箱，点击 **Get your API key**
> 3️⃣ 检查邮箱，点击邮件里的确认链接
> 4️⃣ 在本机终端配置 API key，避免把密钥贴到聊天或提交到仓库
>
> 💡 免费额度：每月 500 张

在本机终端保存：
```bash
python3 "<SKILL_DIR>/scripts/compress.py" --set-api-key "用户的KEY"
```

### 关于 `<SKILL_DIR>`

`<SKILL_DIR>` 指当前 `SKILL.md` 所在目录。请用实际路径替换命令里的 `<SKILL_DIR>`。

---

## Step 2：理解用户意图（5 维分解法）

把任何一句话拆解成下面 5 个维度，对照 Step 5 速查表组装命令：

| 维度 | 默认 | 用户怎么改变 |
|------|------|-------------|
| **源文件夹** | 必填，没说就问 | "处理 xxx 文件夹" |
| **是否覆盖原图** | 普通压缩使用 `--output` 指向独立目录。直接运行脚本且不传 `--output` 时，普通压缩会原地覆盖 | 明说 "覆盖原图" / "原地" → 不传 `--output`，并加 `--backup` |
| **变换内容** | 仅压缩 | resize / preset / multi-size / convert |
| **保留元数据** | 全剥离 | "保留拍摄时间 / GPS" → `--preserve` |
| **过滤条件** | 全部图片 | "跳过 xxx" → `--exclude` |

**关键陷阱**：
- 路径含空格 / 中文 → 命令里**必须双引号**包起来（`"<F>"` 不是 `<F>`）
- `--multi-size` 多个值 → 逗号分隔**无空格**（`xiaohongshu,instagram-square` 不是 `xiaohongshu, instagram-square`）
- `--width` `--height` `--workers` 是数字 → **不带引号**
- 颜色 / 路径含 `#` 或空格 → 用引号（`"#FFFFFF"`、`"~/My Photos"`）

---

## Step 3：配额护栏（执行前的安全计算）

### 3a. 估算公式

```
本次 API 调用数 = 待处理图片数 × 预设数 × 格式数
```

| 操作 | 倍数 | 80 张图举例 |
|------|------|-----------|
| 单一压缩 / 缩放 / 单格式 | 1× | 80 次 |
| `--multi-size all-social` | 6× | 480 次 |
| `--multi-size all-social --convert webp,avif` | 12× | 960 次 ⚠️ 超月配额 |
| `--multi-size twitter-pack --convert webp` | 4× | 320 次 |

### 3b. 何时必须停下问用户（不要"自动继续"）

| 触发条件 | 必问内容 | 用户答 "是/继续/确认" 才执行 |
|---|---|---|
| 用户要**覆盖原图**且**没加 `--backup`** | "你确定要直接覆盖原图、不留备份吗？建议加 `--backup` 保留副本。" | 加 `--backup` 或显式确认 |
| 估算调用数 **>100** | "本次 N 张要 N 次 API 调用，先 `--dry-run` 看清单？" | dry-run 确认或显式 "直接跑" |
| 估算调用数 **>本月剩余配额**（用 `--show-config` 提前看已用） | "免费版每月 500 张，本次需 N 张，可能不够。要分批/换账号/继续？" | 用户做选择 |
| **首次为该用户处理** | "TinyPNG 是有损压缩，第一次处理建议先备份原图，要继续吗？" | 用户确认 |
| 用户用 `--force` 重做 **>50 张** | "强制重做会重新消耗 API 配额，确认吗？" | 用户确认 |

**重要**：上述场景中**禁用** "我马上开始" "这就帮你处理" 等措辞 —— 必须用问号结尾，等用户答复。

---

## Step 4：执行 + 展示

### 4a. 常规执行话术

> ⏳ 即将处理 12 张图，生成小红书 3:4 版本到 `xxx_xiaohongshu/`，预计 12 次 API 调用，4 worker 并发约 4 秒。

### 4b. 展示结果（成功）

脚本最后会打印 Markdown 表格 + 合计行 + 配额 + 总耗时。默认**不会**生成 `_report.md`；只有用户明确要求保存报告时才加 `--write-report`。**原样贴出表格**（不要重写、不要省略），然后一句话收尾：

> 🎉 处理完成！本次共节省 X.XX MB（YY.Y%），用时 0:42。
> 💡 想看效果可以打开 `<output>` 文件夹对比

### 4c. 展示结果（失败 / 部分失败）

失败的行状态是 `❌` 或 `❌ 配额` / `⏸️ 跳过`。按场景对话：

**部分失败**（少数几张失败，多数成功）：
> ⚠️ 完成了 N/M 张，有 X 张失败：[列出失败文件名]
> 失败原因：[根据 error_type 总结，如"网络超时" / "格式异常" / "TinyPNG 服务暂不可用"]
> 要重试失败的吗？我可以加 `--no-overwrite` 跳过已成功的，只重做失败的。

**全部失败**（无一成功）：
> ❌ 全部失败，看起来是系统性问题：
> - 网络问题？请检查能否打开 https://tinypng.com
> - API key 失效？跑 `--show-config` 看看
> - 文件本身损坏？挑一张丢进 https://tinypng.com 网站测一下

**配额耗尽**（退出码 6）：
> 🚨 本月 500 张免费配额用完了。可选：
> 1️⃣ 等下个月（每月 1 号重置）
> 2️⃣ 升级 TinyPNG 付费版（$9 起，1500 张/月）
> 3️⃣ 用 `--unset-api-key` 切换到另一个账号
> 已成功处理 N 张保留在输出目录，没有损坏。

---

## Step 5：命令速查表

> 下面 `<S>` = `<SKILL_DIR>/scripts/compress.py`，`<F>` = 用户的文件夹路径（必须双引号）。

| 用户说 | Claude 调用 |
|--------|-------------|
| **基础** |
| 压缩这个文件夹 | `python3 "<S>" "<F>" --output "<F>_compressed"` |
| 原地压缩但保留原图副本 | `python3 "<S>" "<F>" --backup` |
| 强制重做（忽略缓存）| `python3 "<S>" "<F>" --output "<F>_compressed" --force` |
| **缩放** |
| 等比缩到 1080 宽 | `python3 "<S>" "<F>" --resize-method scale --width 1080` |
| 缩到 1080×1080 不变形 | `python3 "<S>" "<F>" --resize-method fit --width 1080 --height 1080` |
| 智能裁切到 1:1 1080 | `python3 "<S>" "<F>" --resize-method cover --width 1080 --height 1080` |
| 智能 300×300 缩略图 | `python3 "<S>" "<F>" --resize-method thumb --width 300 --height 300` |
| **社交平台预设** |
| 小红书 | `python3 "<S>" "<F>" --preset xiaohongshu` |
| 公众号封面 | `python3 "<S>" "<F>" --preset wechat-cover` |
| 朋友圈方图 | `python3 "<S>" "<F>" --preset moments` |
| IG 方图 | `python3 "<S>" "<F>" --preset instagram-square` |
| IG Story / Reels | `python3 "<S>" "<F>" --preset instagram-story` |
| Twitter 推文 | `python3 "<S>" "<F>" --preset twitter-post` |
| Twitter 头图 | `python3 "<S>" "<F>" --preset twitter-header` |
| 抖音 | `python3 "<S>" "<F>" --preset douyin` |
| **多尺寸** |
| 一键全平台 | `python3 "<S>" "<F>" --multi-size all-social` |
| 国内全平台 | `python3 "<S>" "<F>" --multi-size zh-social` |
| 海外全平台 | `python3 "<S>" "<F>" --multi-size global-social` |
| 全套小红书 | `python3 "<S>" "<F>" --multi-size xhs-pack` |
| 全套微信 | `python3 "<S>" "<F>" --multi-size wechat-pack` |
| 全套 Instagram | `python3 "<S>" "<F>" --multi-size instagram-pack` |
| 全套 Twitter | `python3 "<S>" "<F>" --multi-size twitter-pack` |
| 自选多尺寸 | `python3 "<S>" "<F>" --multi-size xiaohongshu,instagram-square,twitter-post` |
| **格式转换** |
| 都转 WebP | `python3 "<S>" "<F>" --convert webp` |
| 都转 AVIF | `python3 "<S>" "<F>" --convert avif` |
| 同时生成 WebP + AVIF | `python3 "<S>" "<F>" --convert webp,avif` |
| 透明 PNG → 白底 JPEG | `python3 "<S>" "<F>" --convert jpeg --background white` |
| 透明 PNG → 黑底 JPEG | `python3 "<S>" "<F>" --convert jpeg --background "#000000"` |
| 自动选最小格式 | `python3 "<S>" "<F>" --convert auto` |
| **元数据** |
| 保留拍摄时间 | `python3 "<S>" "<F>" --preserve creation` |
| 保留时间 + GPS | `python3 "<S>" "<F>" --preserve creation,location` |
| 保留全部 | `python3 "<S>" "<F>" --preserve all` |
| **过滤 / 性能** |
| 跳过缩略图 | `python3 "<S>" "<F>" --exclude "*.thumb.*,*-small.*"` |
| 跳过已存在的输出 | `python3 "<S>" "<F>" --output ... --no-overwrite` |
| 串行处理（更稳）| `python3 "<S>" "<F>" --workers 1` |
| 加速到 8 worker | `python3 "<S>" "<F>" --workers 8` |
| **复合** |
| 小红书 + WebP + 留拍摄时间 | `python3 "<S>" "<F>" --preset xiaohongshu --convert webp --preserve creation` |
| 全平台 + WebP + 跳过已存在 | `python3 "<S>" "<F>" --multi-size all-social --convert webp --no-overwrite` |
| **预演 / 工具** |
| 预演 | 在任何命令尾加 `--dry-run` |
| 看所有预设 | `python3 "<S>" --list-presets` |
| 看当前配置 | `python3 "<S>" --show-config` |
| 切换账号 | `python3 "<S>" --unset-api-key` 然后 `--set-api-key NEW` |

---

## Step 6：复合请求拆解决策树

用户的话经常包含多个意图，按下面顺序逐一识别：

```
1. 源文件夹？     → 没说就先问
2. 输出位置？     → 普通压缩用 --output；用户明说"覆盖" → 不传 --output 并加 --backup
3. 缩放/裁切意图？ → 关键词："缩"、"裁切"、"做 [平台]"、"全平台" → preset / multi-size / resize-method
4. 格式转换？     → 关键词："转 X"、"换成 X"、"X 格式" → --convert
5. 元数据保留？   → 关键词："留时间"、"留 GPS"、"保留 EXIF" → --preserve
6. 过滤条件？     → 关键词："跳过"、"排除"、"除了"、"忽略 thumb" → --exclude
7. 性能/重做？    → 关键词："快点"、"慢点"、"重做"、"忽略缓存" → --workers / --force
```

**例子**：用户说"把这些 iPhone 客片都做成小红书 + 朋友圈 + IG 三个版本，转 WebP，保留拍摄时间，存到桌面 client-out 文件夹"

拆解：
- 源 = 用户提供的 iPhone 文件夹（含 HEIC，自动处理）
- 输出 = `~/Desktop/client-out`（用户明指 → 不自动）
- 变换 = `--multi-size xiaohongshu,moments,instagram-square` 或 `--multi-size all-social` 取部分
- 格式 = `--convert webp`
- 元数据 = `--preserve creation`

最终命令：
```bash
python3 "<S>" "<iPhone 源>" \
  --multi-size xiaohongshu,moments,instagram-square \
  --convert webp --preserve creation \
  --output "~/Desktop/client-out"
```

调用数估算：图片数 × 3 预设 × 1 格式 = 3× 调用。如果有 50 张 → 150 次 → 触发"必问"阈值。

---

## 完整对话样板（Few-Shot）

### 样板 A：简单需求 + 首次使用

> **用户**："把 ~/Desktop/baby 这个文件夹的图都压一压"
>
> **Claude**：
> （检查 → 已有 key、tinify 已装）
> 这是第一次帮你压缩，提醒一下：TinyPNG 是有损压缩、会原地覆盖原文件。建议二选一：
> 1. 加 `--backup` 自动备份原图（推荐）
> 2. 我先帮你建一个 `~/Desktop/baby_compressed` 输出目录，原图不动
>
> 你倾向哪种？

---

### 样板 B：复合需求 + 大量 API 调用

> **用户**："iPhone 拍的这些客片，给我做小红书 + 朋友圈 + IG，都转 WebP，存到 desktop/client"
>
> **Claude**：
> （扫描 → 80 张含 HEIC）
> 解析了一下你的需求：
> - 源：80 张 iPhone 照片（含 HEIC，会自动转 JPEG）
> - 输出：`~/Desktop/client/`（小红书/朋友圈/IG 三个子目录）
> - 操作：缩放 + WebP 转换
> - 估算 API 调用：80 × 3 预设 × 1 格式 = **240 次**
>
> 跑 `--show-config` 看你本月已用配额…[执行] 已用 30/500，剩余 470，本次 240 够用。
>
> 你确认开跑吗？跑了大概需要 1-2 分钟（4 worker 并发）。

---

### 样板 C：失败处理

> **用户**："为什么有 5 张失败？"
>
> **Claude**：
> （查看输出，发现都是 ServerError）
> 5 张全是 TinyPNG 服务端错误（不是你的问题），可能是当时网络抖了一下。
> 我可以重试失败的：
> ```bash
> python3 "<S>" "<F>" --output ... --no-overwrite
> ```
> 加了 `--no-overwrite`，已经成功的 75 张会被跳过，只重做失败的 5 张，不会浪费配额。要试吗？

---

## 附录

### 内置预设清单

| 平台 | 预设 |
|------|------|
| 小红书 | `xiaohongshu` (1080×1440 fit) · `xiaohongshu-square` (1080×1080 fit) |
| 微信 | `wechat-cover` (900×383 cover) · `wechat-content` (900 scale) · `moments` (1080×1080 fit) |
| Instagram | `instagram-square` · `instagram-portrait` (1080×1350 fit) · `instagram-story` (1080×1920 cover) |
| Twitter / X | `twitter-post` (1600×900 fit) · `twitter-square` · `twitter-portrait` · `twitter-header` (1500×500 cover) · `twitter-card` (1200×628 cover) |
| 微博 | `weibo` (1242×1660 fit) |
| 抖音 / 快手 | `douyin` (1080×1920 cover) |
| 缩略图 | `thumb-300` (300×300 thumb) |

**Bundle**：`all-social` · `xhs-pack` · `wechat-pack` · `instagram-pack` · `twitter-pack` · `zh-social` · `global-social`
完整：`python3 <S> --list-presets`

### 退出码

| 码 | 含义 | Claude 应做 |
|:--:|------|------------|
| 0 | 成功 | 展示结果 |
| 1 | 文件夹不存在 / 不是目录 | 让用户重新确认路径 |
| 2 | 缺 `tinify` | 装包后重试 |
| 3 | API key 无效 | 引导重新获取 |
| 4 | 未配置 API key | 走 Step 1b 引导 |
| 5 | 缺必填参数 | 询问文件夹 |
| 6 | TinyPNG 配额超限 | 用 Step 4c "配额耗尽"话术 |
| 7 | 参数错误（非法预设/格式/组合冲突）| 按报错信息修复 |
