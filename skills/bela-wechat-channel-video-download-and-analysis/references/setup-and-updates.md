# 第一次处理视频号链接

调用时先运行下文个人配置的 `init`。只收到技能名时请用户贴作品分享链接；仅查看或更改偏好时可以直接处理。拿到有效链接后，优先使用当次指定的下载器，其次读取 `download.provider`。两者都为空时按下列顺序询问，等用户确认。已有偏好就直接沿用。

- **红狐（推荐）`wechat-video-downloader`** 会把分享链接发给红狐解析，使用用户自己的红狐 API Key，受账号额度限制。[红狐使用说明](https://github.com/redfox-data/redfox-community/blob/main/skills/wechat-video-downloader/SKILL.md)
- **乔木 `qiaomu-download`** 优先通过本机微信获取。需要使用乔木在线解析时，先征得用户对本次转交链接的同意。

首次选定后保存为常用下载器。用户说「仅这次」时只覆盖本次。只准备本次选中的下载器，已可用的安装直接复用。解析失败时报告该下载器返回的原因，等用户明确选择后才能改用另一家。用户只要成片时用下载模式。选择飞书或两处时，先取得用户提供的目标链接。已有常用链接可直接沿用。归档文件就绪后再按[飞书归档](lark-archive.md)读取该目标。

## 查现有安装

从 Agent 提供的 `SKILL.md` 文件路径取得实际安装目录 `SKILL_DIR`。以下命令中的 `python3` 可以换成当前可用的 Python 3 解释器（例如项目 venv 的绝对路径）。脚本的位置、项目根目录和成品保存目录可以各不相同。

```sh
python3 "$SKILL_DIR/scripts/check_dependencies.py"
# 用户本次指定红狐且只要视频时
python3 "$SKILL_DIR/scripts/check_dependencies.py" --download-provider wechat-video-downloader --download-only
# 云电脑从临时目录启动任务时，加 --workspace "$PROJECT_DIR" 指向实际项目根目录
# Agent 给出了依赖 Skill 的挂载目录时，加 --skill-root "$DEPENDENCY_DIR"（可重复）
# 如有用户指定的配置，加 --config "$CONFIG_FILE"
```

未选下载器时脚本返回 `status: download_provider_required` 并以 2 退出，应先询问选择。选定后读取 JSON 的 `download_provider`、`checks` 和 `missing_dependencies`。每项由 `dependency` 标识。从 `skill:<所选下载器名称>` 项的 `path` 取得上游目录。完整拆解还需读取 `tool:hypit` 的 `path`。`tool:python3.path` 是执行预检的同一解释器，后续用它运行下载脚本。如果 FFmpeg 等工具只在 `~/.local/bin` 等目录被找到，将相应目录加入下载进程的 PATH。预检只核对本地入口，实际媒体获取、识别和归档分别在使用时验证。

先使用当次 `--skill-root`、配置中的 `skill_roots`，再查工作区、Bela 安装目录的同级 Skill 和用户级目录。项目内识别 `.agents/skills`、`.claude/skills`、`.gemini/skills` 和 `.grok/skills`；从 Git 项目的子目录启动会查到该项目根。非 Git 项目或从其他工作区启动时可直接传 `--workspace`。用户级支持同名目录以及 `$CODEX_HOME/skills`、`$CLAUDE_CONFIG_DIR/skills`、`$GROK_HOME/skills`。skills CLI 的 Grok Build 安装目标使用 `.grok/skills`；Grok Bot 云电脑可使用通用 `.agents/skills`。若托管 Agent 使用其他挂载目录，把平台实际给出的技能目录或其父目录传给 `--skill-root`；长期复用时可记入 `skill_roots`。[Codex Skills](https://developers.openai.com/codex/skills/) · [Claude Code Skills](https://code.claude.com/docs/en/skills) · [Gemini CLI Skills](https://geminicli.com/docs/cli/skills/) · [skills CLI 支持的 Agent](https://github.com/vercel-labs/skills#supported-agents)

## 补齐本次所需项

按当前主机、安装器和使用范围执行缺少项对应的命令。安装完成后重跑同一个检查。已有安装不在 PATH 时先定位实际 launcher；对解包不完整的 Skill，从原渠道修复。用用户自己的包管理器和可写范围安装。需要管理员权限时说明具体动作，取得授权或让用户完成该步。

| 缺少项 | Agent 的处理 |
| --- | --- |
| Python 或安装工具 | 乔木需 Python 3.10+，红狐适配器需 Python 3.8+ 和同一解释器中的 `requests`。缺少 `requests` 时可在任务 venv 里运行 `python3 -m pip install requests`，激活该环境后复检并运行下载。选用 `npx skills add` 补装 Skill 时才需 npx。用 npm 安装 Hypit 时按所选发布版准备兼容 Node.js 和 npm。现有 Hypit 能运行媒体命令时直接复用。 |
| qiaomu-download | 在用户的任务项目中运行 `npx skills add joeseesun/qiaomu-download --skill qiaomu-download -y`。沿用现有 Agent 和项目或全局范围；用户级安装才加 `-g`。首次用 npx 时可设 `npm_config_yes=true` 允许获取 skills CLI。安装后读取 `SKILL.md` 和 `references/wechat-video.md`。[上游安装说明](https://github.com/joeseesun/qiaomu-download) |
| wechat-video-downloader | 在任务项目运行 `npx skills add https://github.com/redfox-data/redfox-community --skill wechat-video-downloader`，选择适用的 Agent 和原安装范围。使用所装目录的 `SKILL.md` 和 `scripts/parse_video_download.py`。[红狐官方目录](https://github.com/redfox-data/redfox-community/tree/main/skills/wechat-video-downloader) |
| FFmpeg、FFprobe | 两条路线都用 FFmpeg / FFprobe 校验和压缩媒体。macOS 已有 Homebrew 时可运行 `brew install ffmpeg`，Linux 可用系统包管理器安装 ffmpeg。将安装目录加入本次进程 PATH 后复检。[FFmpeg 分发](https://ffmpeg.org/download.html) |
| Hypit Skill | 完整拆解时运行 `npx skills add hypit-ai/hypit --skill hypit -y`，沿用当前安装范围。读取所装版本中的 `references/creation/reference-video.md`。[官方安装说明](https://github.com/hypit-ai/hypit/blob/main/docs/guide/skill.md) |
| Hypit CLI | 优先用配置或现有项目的 `node_modules/.bin/hypit`。用户级 npm 前缀可写时运行 `npm install --global @hypit/hypit`；若默认前缀需提权，可执行 `npm install --global --prefix "$HOME/.local" @hypit/hypit`，将 `~/.local/bin` 加入本次 PATH。用 `hypit media --help` 核实媒体入口可用。[Hypit 分发说明](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/environment/distribution.md) |
| 本地 Whisper | 默认识别方式。已有 uv 时可用 `uv tool install --python 3.11 openai-whisper`，有 pipx 时可用 `pipx install openai-whisper`。也可以用兼容 Python 创建用户目录内的 venv，再用该 venv 的 pip 安装 `openai-whisper`，把 `tools.whisper` 指向其 CLI。[Whisper 安装说明](https://github.com/openai/whisper#setup) |

相应工具已就绪就继续所选任务。需要补装、实跑发现版本不兼容或用户要求更新时，按[定向更新](skill-updates.md)只核对涉及的依赖。乔木报告本地微信未连接时，按所安装版本处理连接、证书信任或系统代理。

红狐解析脚本从进程环境读取 `REDFOX_API_KEY`。用户可在红狐账号中获取 Key，再通过自己的运行环境或凭据管理器提供给脚本。即便使用 OpenClaw 配置，运行脚本的进程也需获得该变量。Bela 的 `download.provider` 字段只保存下载器名称。遇到缺少凭据、无效链接或额度不足时报告具体原因，保留当前下载器和工作目录。[红狐脚本](https://github.com/redfox-data/redfox-community/blob/main/skills/wechat-video-downloader/scripts/parse_video_download.py) · [获取 API Key](https://redfox.hk/settings/api-keys?source=github)

### 准备用户选定的 Whisper 模型

有可读的指定 `model_path` 或现成缓存就复用。第一次按模型名准备时，使用安装了 **openai-whisper** 的 Python 解释器。uv 管理的环境可通过 `uv tool dir` 找到其中的 `openai-whisper/bin/python`，venv 安装用其 `bin/python`。Windows 下使用对应环境的 `Scripts/python.exe`。取 `WHISPER_MODEL` 自配置（默认 `small`）。以下命令使用官方模型表、下载校验与 CPU 加载，复用 Whisper 缓存。

```sh
"$WHISPER_PYTHON" -c 'import sys, whisper; name = sys.argv[1]; assert name in whisper.available_models(), name; whisper.load_model(name, device="cpu")' "$WHISPER_MODEL"
```

显式自定义模型路径丢失时，沿原来源修复或请用户定位，以免改用另一个模型。已选择 `hypit-transcribe` 时跳过本地 Whisper 安装，按[Hypit 分析](hypit-analysis.md)验证已有 Profile、endpoint 和相应服务授权。

## 个人配置与旧版迁移

设置保存在当前系统用户的 `~/.bela-skills-config/bela-wechat-channel-video-download-and-analysis.config`（UTF-8 JSON，`schema_version: 2`）。第一次调用本技能即运行 `init`，包括仅打开技能、尚未给链接的情况。该步骤只准备个人配置。收到链接后再准备下载和分析依赖。换项目或更新 Skill 后继续使用同一份文件。

```sh
python3 "$SKILL_DIR/scripts/user_config.py" init
python3 "$SKILL_DIR/scripts/user_config.py" show
python3 "$SKILL_DIR/scripts/user_config.py" set --download-provider qiaomu-download
python3 "$SKILL_DIR/scripts/user_config.py" set --download-provider wechat-video-downloader
python3 "$SKILL_DIR/scripts/user_config.py" set --download-provider ask
python3 "$SKILL_DIR/scripts/user_config.py" set --mode local --local-root "$HOME/视频研究"
python3 "$SKILL_DIR/scripts/user_config.py" set --mode feishu --feishu-parent-url "$FEISHU_PARENT_URL"
python3 "$SKILL_DIR/scripts/user_config.py" set --mode both
python3 "$SKILL_DIR/scripts/user_config.py" destination
# 仅本次换到另一个飞书位置
python3 "$SKILL_DIR/scripts/user_config.py" destination --mode both --feishu-parent-url "$FEISHU_PARENT_URL"
python3 "$SKILL_DIR/scripts/user_config.py" set --mode ask
python3 "$SKILL_DIR/scripts/user_config.py" set --clear-local-root --clear-feishu-parent-url
```

如果 `show` 或 `set` 返回 `preferences_read_only`，可继续使用能读取的已存设置。本次明确选择分别传给 `check_dependencies.py --download-provider` 和 `user_config.py destination --mode`（需要时加 `--feishu-parent-url`）。只读环境下无法记住新选择；需要跨任务保存时，将可写的持久卷挂载或链接到 `~/.bela-skills-config/`。已有配置损坏时向用户说明原文件的问题。

`init`、`show` 和 `set` 返回 `{ok,path,config}`。首次选择或明确更改常用下载器时用 `set --download-provider` 保存名称。「忘记下载器」用 `set --download-provider ask` 将其重置为 `null`。临时覆盖只向依赖检查传 `--download-provider` 并按本次选择下载。保存位置由 `config.delivery` 单独管理。`--mode ask` 让下次再问保存方式，保留已有根目录和父链接。清空本地根目录恢复建议位置；清空飞书父链接后，下次选择飞书或两处时重新向用户要链接。设置命令只合并给出的字段。提供的新飞书链接会先验证 HTTPS、官方域名与资源路径，查询串和片段会移除。认证仍由飞书 CLI 管理。

`destination` 仅读取偏好并校验本次输入。未选方式时返回 `delivery_mode_required`，选择飞书或两处但缺链接时返回 `feishu_parent_url_required`，当次传入的链接无效时返回 `invalid_feishu_parent_url`。三种情况都以 2 退出，提示用户补充对应信息。返回 `destination_ready` 只表示本次位置已选好，远端可访问性在成品就绪后用本机 CLI 核实。

首次创建时从原 Skill 的 `config.local.json` 迁移已知工具路径、转录选择和公开来源记录。旧版明确配置的父 Wiki 链接可带入，旧样例的个人知识库名不会成为用户默认位置。原先相对于旧配置的 Skill 搜索目录会转换为绝对路径。后续只读个人配置。文件损坏时保留原文件并返回错误。需要临时指定工具配置时，向依赖检查脚本传 `--config "$CONFIG_FILE"`，该调用仅检查所给 v1/v2 文件。

| 字段 | 用法 |
| --- | --- |
| `download.provider` | 新配置或缺少此字段的旧配置按 `null` 处理，首次下载时先推荐红狐，等用户选择。可保存 `wechat-video-downloader`（红狐）或 `qiaomu-download`（乔木）。 |
| `delivery.mode` | 首次为 `null`，询问本地、飞书或两处。已选的默认方式保存为 `local`、`feishu` 或 `both`。 |
| `delivery.local_root` | 默认 `~/视频号爆款拆解`，接受绝对路径或 `~/` 开头的路径。 |
| `delivery.feishu_parent_url` | 默认 `null`，表示用户尚未指定位置。选择飞书或两处时必须有用户给出的链接。支持飞书或 Lark 的文件夹、Wiki 节点，以及可核实归档位置的文档 HTTPS 链接。 |
| `transcription.mode` | 默认 `whisper-local`，另支持明确选择的 `hypit-transcribe`。 |
| `transcription.language / threads` | 默认中文 `zh`、4 个 CPU 线程，按实际主语言和本机设置调整。 |
| `transcription.model / model_path` | 默认多语言 `small`。按绝对路径、`WHISPER_MODEL_PATH`、命名模型缓存的顺序解析；默认缓存受 `XDG_CACHE_HOME` 支持。 |
| `transcription.runtime_profile / endpoint` | Hypit 转录模式的已选 Profile 绝对路径与 endpoint 名。 |
| `tools.hypit / tools.whisper` | 选定 CLI 的绝对路径。留空时自动查找常用命令目录，Hypit 也查当前项目安装。 |
| `skill_roots` | 自定义或托管 Agent 挂载的 Skill 根目录列表，可给技能集合目录或具体 Skill 的目录，相对路径以配置文件所在目录为准。 |
| `skill_sources` | 安装器记录不足时补充已核实的来源和范围；只记录公开来源、ref 和追踪标识。 |
