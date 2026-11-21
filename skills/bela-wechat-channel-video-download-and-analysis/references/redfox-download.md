# 用红狐下载一条视频号作品

按主文选定红狐路线后，将本条分享链接发给红狐解析。请求使用用户自己的红狐账号，可能消耗积分。每条作品单独准备源文件目录。重试前核对已有收据的分享链接、文件路径和 SHA-256，能复用原片就直接进入下一步。

## 安装与鉴权

需要 Python 3.8+、该解释器可导入的 `requests`、FFmpeg、FFprobe，以及红狐的 `wechat-video-downloader`。从已选路线的依赖检查结果中取 Skill 路径 `REDFOX_DIR`。缺少上游 Skill 时，在任务项目运行以下命令。

```sh
npx skills add https://github.com/redfox-data/redfox-community --skill wechat-video-downloader
```

选择当前 Agent 与安装范围。缺少 `requests` 时可在项目虚拟环境安装，后续用同一解释器执行适配器。上游脚本读取进程环境变量 `REDFOX_API_KEY`。如未配置，引导用户在红狐获取密钥并通过自己的运行环境注入，重新启动或刷新当前 Agent 的环境。密钥由使用者管理，配置文件、聊天、日志和收据只记录是否就绪。[红狐密钥管理](https://redfox.hk/settings/api-keys?source=github)

## 下载与核验

用依赖检查通过的 Python 执行。此处的 `SOURCE_DIR` 是单条作品的工作目录，临时直链在适配器进程内使用。

```sh
python3 "$SKILL_DIR/scripts/redfox_download.py" \
  --url "$SHARE_URL" --redfox-dir "$REDFOX_DIR" --source-dir "$SOURCE_DIR"
```

适配器调用已安装的 `scripts/parse_video_download.py`。上游向 `https://redfox.hk/story/api/parseWork/videoDownload/sph` 发出带 `X-API-KEY` 的 POST，读取 `title` 或 `desc`、`cover`、`videoUrl`。若视频地址为空，上游会尝试 `resources[0].downloadUrl`。上游返回临时地址，Bela 随即下载到本地。[上游工作流](https://github.com/redfox-data/redfox-community/blob/0750a5e651cae9f506592abffea2efacaf2a5bfd/skills/wechat-video-downloader/references/core_workflow.md) · [解析脚本](https://github.com/redfox-data/redfox-community/blob/0750a5e651cae9f506592abffea2efacaf2a5bfd/skills/wechat-video-downloader/scripts/parse_video_download.py)

- 成功时退出码为零且 `ok: true`。读取 `video_path`、`video_sha256` 和 `probe`。适配器对临时文件运行 FFprobe 解码计帧，核实时长、视频流和画面尺寸，记录帧率及音轨编码，再将已验证的原片保存为 `redfox-source.mp4`。按主文的命名脚本生成交付文件名。
- `title` 是标题或描述的首个非空行，`description_or_title` 保留上游返回的文字。红狐脚本没有博主署名字段，`author` 留空。若归档所需署名或标题仍缺，按主文核实。
- `cover_path` 是同一条解析结果的 `cover` 字段所指的本地候选图。适配器仅接受公网 HTTPS 图片和跳转，检查图像编码、尺寸和可解码性。目检核实确属作品发布封面后，按[媒体归档规范](media.md)纳入交付。缺图、读取失败或归属不明时继续用已验证的视频。

## 失败时按阶段处理

| 返回状态 | 处理 |
| --- | --- |
| `missing_redfox_skill`、`missing_requests`、`missing_ffmpeg_or_ffprobe` | 补齐所选路线依赖后重试。 |
| `missing_api_key`、`authentication_failed` | 请用户在自己的环境配置或更新红狐凭据，或按主文另选下载方式。 |
| `insufficient_credit` | 说明本次解析因积分或额度不足停止，由用户决定是否调整账号额度或更换路线。 |
| `rate_limited`、`resolver_network_error`、`resolver_failed`、`invalid_resolver_response` | 记录解析阶段的类别。检查本条分享链接及服务状态，再按本次授权决定是否重试。 |
| `media_http_error`、`incomplete_download`、`invalid_media_url`、`invalid_mp4`、`download_failed` | 临时地址可能过期，服务也可能返回错误页或无法解码的素材。报告下载或验证失败，需要重新解析时说明可能再次消耗积分。 |
| `destination_exists` | 核对原收据及哈希，或使用新工作目录。已有文件保留。 |

只有通过本地视频验证才进入拆解。收据保存适配器返回的分享链接与本地信息，省略上游原始响应、临时下载地址和密钥。
