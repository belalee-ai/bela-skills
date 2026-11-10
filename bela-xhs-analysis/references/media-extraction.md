# 笔记媒体内容深度提取

把发布文案（desc）之外的真实内容也拿到——图文笔记的图片内文字、视频笔记的口播逐字稿。

## 何时触发

| 笔记类型 | 必跑模块 |
|---------|---------|
| `type=normal`（图文） | `ocr_images.sh` |
| `type=video`（视频） | `transcribe_video.sh` |
| `type=mix`（极少见，图 + 视频） | 两个都跑 |

单篇分析模式默认跑；博主分析的 TOP N 笔记默认跑；多篇汇总模式询问用户。

## 前置依赖

```bash
# OCR (macOS Vision Framework)
command -v swift && command -v ffmpeg

# 视频转写
command -v whisper-cli
test -f "${WHISPER_MODEL_PATH:-$HOME/.whisper-models/ggml-large-v3-turbo-q5_0.bin}"
```

任一缺失时引导用户安装：

```bash
brew install whisper-cpp ffmpeg
mkdir -p ~/.whisper-models
curl -L -o ~/.whisper-models/ggml-large-v3-turbo-q5_0.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
```

模型 547MB，仅首次下载。`WHISPER_MODEL_PATH` 环境变量可自定义路径。

## 图片 OCR

**脚本**：`scripts/media/ocr_images.sh`

**接口**：

```bash
# 方式 1: stdin (一行一个 URL 或本地路径)
echo -e "url1\nurl2" | ocr_images.sh --out result.txt

# 方式 2: URL 列表文件
ocr_images.sh --urls-file urls.txt --out result.txt

# 方式 3: 本地路径参数
ocr_images.sh img1.png img2.png

# 方式 4: 混合
ocr_images.sh "https://cdn.../img.webp" local.png
```

**输出格式**：

```
=== <path-or-url> ===
（该图完整 OCR 文本）

=== <path-or-url> ===
（下一张）
```

**支持格式**：webp（自动转 png）、jpg、png。

**性能**：9 张图约 8 秒（Apple Silicon Vision Framework）。

**准确率**：中文 + 中英混排 ★★★★☆，标点 / 章节符号 / 项目符号都能识别；偶发英文短词误识（如 "loop" → "lo0p"），需要轻度人工校对。

## 视频口播转写

**脚本**：`scripts/media/transcribe_video.sh`

**接口**：

```bash
# 输入: 视频文件 OR 直链 URL
transcribe_video.sh /path/to/video.mp4
transcribe_video.sh "https://sns-video-alos.xhscdn.com/.../xxx.mp4?sign=..."

# 落盘
transcribe_video.sh video.mp4 --out transcript.txt

# 指定语言
transcribe_video.sh video.mp4 --lang zh|en|auto
```

**输出格式**：每行一句口播文案。

**性能**：3 分钟视频约 14 秒（Apple Silicon Metal 加速）。

**准确率**：中文 ★★★★★，远高于字幕帧 OCR。

## 视频 src 的两种形态

调用 `transcribe_video.sh` 前，先判断 video 元素的 src：

| 形态 | 处理 |
|------|------|
| **CDN 直链**（`https://sns-video-*.xhscdn.com/...mp4?sign=...`） | 直接传给脚本（脚本内部 curl） |
| **Blob URL**（`blob:https://www.xiaohongshu.com/...`） | 浏览器内 fetch 落盘后传本地路径 |

Blob 下载优先使用 `agent-reach` 获取页面和媒体信息；需要在页面内执行 fetch 时使用 `agent-browser`，需要复用用户浏览器登录态时使用 `bb-browser fetch`。

## 跨平台延展

这两条 pipeline **不绑定小红书**：

| 平台 | 视频 src 获取 | OCR 输入 |
|------|--------------|---------|
| 小红书 | DOM `<video>.src` | imageList URL |
| 抖音 | DOM `<video>.src`（多为 blob） | 单图笔记的图片 URL |
| 视频号 | DOM `<video>.src` | — |
| B 站 | DASH 流，需 yt-dlp | — |
| YouTube | 已有 `baoyu-youtube-transcript`，无需重做 | — |

加新平台时，只需在调用方搞定"如何拿到 video URL / image URL"，pipeline 不变。

## 输出质量铁律

**原始数据全量保留，结构化汇总放在下方且明确标注**。

❌ 错误示范：
> 第 6 页 — Prompt 全文（rate limiter 解说）

✅ 正确示范：
> **第 6 页 - 完整内容**
> ```
> Prompt：「我搞不懂我们的 rate limiter 是怎么工作的。请阅读相关代码，产出一份 HTML 解说页：token-bucket 流程图、3-4 段关键代码加注释、底部加一个 gotchas 区块，按一次性阅读优化。」
> ```

这条铁律避免"中间产物对 ≠ 交付对"的失误。

## 已知陷阱

- bash 3.2（macOS 默认）对空数组的 `${arr[@]:-}` 展开会产生空字符串元素，触发 curl "blank argument" 报错。脚本已用 `${#arr[@]} -gt 0` 守卫
- 同一笔记的 imageList 偶尔会出现重复 URL（小红书 SSR 数据 quirk），下载前用 MD5 去重可省时间
- whisper-cli 对极短音频（<3 秒）可能返回空，需 fallback 处理
- 非 macOS 系统目前无内置 OCR 路径，需补 PaddleOCR / Tesseract 实现（未来扩展点）
