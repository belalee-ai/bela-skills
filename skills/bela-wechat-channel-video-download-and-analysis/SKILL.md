---
name: bela-wechat-channel-video-download-and-analysis
description: 下载微信视频号作品，用本地 Whisper 校对口播，用 Hypit 按时间轴做带图拆解，交付 MP4、口播稿、拆解报告和可取得的作品封面。用户只贴 weixin.qq.com/sph/ 链接、要求只下载该视频号到本地、要带图拆解或明确点名时使用。可选本地文件或飞书链接。
metadata:
  version: "2.1.1"
---

# 贝拉 · 视频号下载与拆解

## 收到请求

启动时先运行 `python3 "$SKILL_DIR/scripts/user_config.py" show`，创建或读取用户主目录下的 `~/.bela-skills-config/bela-wechat-channel-video-download-and-analysis.config`（UTF-8 JSON）。仅查看或修改偏好时直接使用 `show` 或 `set` 并回读指定字段，无需作品链接。开始下载和拆解时按以下顺序执行。

1. 接受一条 `https://weixin.qq.com/sph/作品ID`，包括分享文字中的链接。明确调用但缺链接时只提示「请粘贴微信视频号分享链接。」拿到链接后再准备工具。同一请求给多条作品链接时，每条单独处理、建目录和报告进度。
2. 有效链接到手后，分别读取下载器 `download.provider` 和交付位置 `delivery.mode`。当次指定优先，其次用已保存的值。只问仍缺的选择；两项都缺就一起问。
   - 首次询问时把「红狐（推荐）」列为第一项，「乔木」列为第二项，等用户明确选择。说明红狐会把分享链接发给红狐，使用自己的 API Key 和账号额度；乔木优先通过本机微信获取。用户选哪项就记住哪项，以后直接沿用。选定后，用 `python3 "$SKILL_DIR/scripts/user_config.py" set --download-provider wechat-video-downloader` 保存红狐；乔木对应 `qiaomu-download`。「以后用……」同样更新默认，「忘记下载器」用 `set --download-provider ask` 清空默认。「仅这次用……」只把选项传给本次依赖检查和下载步骤。询问时说明选定的下载器今后如何处理分享链接。
   - 保存方式可选本地、飞书或两处。本地使用 `delivery.local_root`（默认 `~/视频号爆款拆解/`）。选择飞书或两处时，优先使用本次给出的飞书目标链接，其次复用用户之前指定的 `delivery.feishu_parent_url`。两者都没有时，直接问「请粘贴你想保存到的飞书文件夹或知识库节点链接。」等用户回复再进行飞书归档。
   - 用 `python3 "$SKILL_DIR/scripts/user_config.py" destination` 核对本次位置。当次指定方式或目标时，分别传 `--mode`、`--feishu-parent-url`。首次收到可用的目标链接或用户说「以后用这里」时，通过 `set --feishu-parent-url "$FEISHU_PARENT_URL"` 记住它；「仅这次」只传给 `destination`。如果收到独立文档链接，先按[飞书归档](references/lark-archive.md)核实并请用户确认父位置，再记住确认的目标。用 `set --mode` 保存常用方式，`set --local-root` 保存本地根目录；`set --mode ask` 恢复询问方式，`set --clear-feishu-parent-url` 让下次飞书交付重新索取目标链接。
   - 两处交付共用一次下载与分析；等待飞书目标时可先完成本地交付。明确只下载时仅准备下载和视频交付所需工具。等待素材或下载失败时，飞书目标核验和登录均留到成品可上传时。
3. 在自己的任务工作区为每条分享链接建独立工作目录。保留来源、未转码的源文件、原始识别和阶段收据。收据只存分享链接、可信作品信息、已核验的本地路径/哈希、飞书目标及返回的文件标识。重复运行按来源和目标作匹配，核实已有文件再续跑。不同来源碰巧同名时保留原目录，询问新的保存名。敏感的临时媒体地址及账号凭据留在下载器内。

## 下载与确认作品资料

按[安装和检查依赖](references/setup-and-updates.md)准备所选下载器，再按[定向更新](references/skill-updates.md)核对它的来源。只走本次选定的一条路线。失败时说明实际原因并保留工作区；用户选用另一家后才切换。

### 红狐 · wechat-video-downloader

首次缺少上游 Skill 时用 `npx skills add https://github.com/redfox-data/redfox-community --skill wechat-video-downloader` 安装。从依赖检查取红狐目录和可导入 `requests` 的 Python，按[红狐下载](references/redfox-download.md)运行适配器。它使用用户本机的 `REDFOX_API_KEY` 向红狐解析当前链接，再把视频及可取得的封面下载到本条作品的工作目录。仅把下载器名称写入偏好。缺少密钥时请用户在本机设置后重试；遇到额度或服务错误时报告原因。红狐返回标题或描述，博主仍需核实。

### 乔木 · qiaomu-download

从依赖检查取得 `$QIAOMU_DIR`，读取已安装的 `$QIAOMU_DIR/references/wechat-video.md`。运行 `python3 "$QIAOMU_DIR/scripts/download.py" download "$SHARE_URL" --dir "$SOURCE_DIR" --single-version`。若返回 `manual_action_required`，提示在电脑微信打开并播放作品，收到「已播放」后加 `--wait-page 90` 继续。首次证书信任、系统代理和许可按上游提示处理。

没有可用本地连接时，说明设置本地后端和使用乔木在线解析器两个选项。只有用户同意**这次**发送分享链接才加 `--wechat-online allowed`。在线下载成功且作品信息仍缺时，可复用本次返回并已获同意的 resolver，运行 `python3 "$SKILL_DIR/scripts/online_metadata.py" --url "$SHARE_URL" --qiaomu-dir "$QIAOMU_DIR" --approved-resolver "$RESOLVER" --source-dir "$SOURCE_DIR"`。本地下载不调用在线补资料接口。

### 两条路线共用的核验与命名

1. 核实取得的本地文件存在且为可解码的视频，用 FFprobe 读取时长、尺寸、帧率和音视频流。通过后再分析。
2. 从同一作品的明确元数据或公开分享页取得博主、原标题。若描述兼作标题，取首个非空行并保留完整描述。作者需有作品署名，不从文件名、人脸、水印或口播猜测。仍缺哪一项就只问哪一项，复用已下载的文件。
3. 原封面可来自下载结果、同一作品的公开分享页或用户。校验能解码、确属该作品、格式与扩展名一致。微信图标、头像、分享卡占位图和视频截帧都不能当作原封面。没有可核验的图时注明「未取得作品原封面」，继续交付。
4. 把完整原标题（含末尾的「。」）传给 `python3 "$SKILL_DIR/scripts/archive_names.py" --url "$SHARE_URL" --author "$AUTHOR" --title "$TITLE"`。取得封面时加 `--cover-ext` 和真实扩展名。目录日期取归档当天的当地日期，重试时复用最初的日期与目录。

## 分析与压缩

按 [Hypit 分析](references/hypit-analysis.md) 在源视频上运行本地 Whisper 和 Hypit。用带时间码的全片画面网格核对段落，细看开场、转折、短促变化和结尾。按烧录字幕与原片校对识别文本及专名。在独立工作目录生成两份符合[报告与口播稿规范](references/report-spec.md)的 Markdown。口播稿保留原话、语义段时间码和待人工校对的词；拆解报告用少量带时间码的证据图说明观察与可借鉴的做法。无音轨或全片确实没有口播时据实写明，并提供有依据的画面时间线。

按[媒体压缩](references/media.md)准备交付版视频、证据图和取得的封面。保留源分辨率、帧率与清晰度，特别查看小字和快速运动片段；仅采用验证通过且体积更小的版本，否则交付下载版。分析始终引用原片时钟。

## 保存与回读

**本地**：在选定根目录下建立单条作品目录。下表名称取自命名脚本，仅目录带日期。报告通过标准 Markdown 相对路径引用 `配图/` 中已压缩的证据图。打开报告逐张验证，整个目录移动后仍可阅读。工作收据和中间产物留在工作区。

| 产物 | 名称 |
| --- | --- |
| 目录 | `MMDD-博主｜标题/` |
| 视频 | `【视频】博主_标题.mp4` |
| 拆解 | `【视频拆解】博主｜标题.md` |
| 口播稿 | `【口播稿】博主｜标题.md`（仅这里去掉标题末尾的「。」） |
| 作品封面（可选） | `【视频号封面】博主｜标题.原图扩展名` |

**飞书**：本次要求的成品就绪，且 `destination` 返回用户指定的目标链接后，才按[飞书归档](references/lark-archive.md)调用本机 `lark-cli`。先以 `--as user` 核实该链接指向的位置，沿用已有登录。只在核实的父位置下建立本条作品目录，上传视频、原生口播稿 Markdown 和取得的封面，用拆解 Markdown 创建飞书文档并嵌入证据图。目标无法访问或归属不明时，提示用户核对权限或提供新的目标链接。回读目录和报告，返回实际链接。

返回用户所选位置的目录与成品链接，注明封面获取情况或实际识别限制。若选了两处，分别报告完成情况。交付到此结束。
