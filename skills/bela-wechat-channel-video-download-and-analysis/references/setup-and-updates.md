# 第一次处理视频号链接

调用时先运行下文个人配置的 `init`。随后从请求中提取作品分享链接；只收到技能名时请用户贴链接。拿到有效链接后由 Agent 安装本次缺少的普通依赖并复检。用户只要视频时用下载模式。用户选本地或尚未选保存位置时，都可以在本地准备素材。选择飞书可以先保存位置偏好。归档所需文件已经就绪后，再按[飞书归档](lark-archive.md)使用本机 CLI 读取目标；下载或分析阶段无需飞书登录。

## 查现有安装

在本次任务工作目录执行。把 `SKILL_DIR` 设为本技能的真实安装目录。安装器范围与下载输出目录分别处理。

```sh
python3 "$SKILL_DIR/scripts/check_dependencies.py"
# 用户明确只要视频时
python3 "$SKILL_DIR/scripts/check_dependencies.py" --download-only
# 如有用户指定的配置，为上述命令添加 --config "$CONFIG_FILE"
```

读取 JSON 的 `checks` 和 `missing_dependencies`。每项由 `dependency` 标识。用 `skill:qiaomu-download.path` 定位上游工具，用 `tool:hypit.path` 调用所选 Hypit。检查通过表示本地程序、所需帮助和文件可访问。成功取得成片、识别和服务调用要分别验证。重复运行时复用已通过的安装和模型。

## 补齐本次所需项

按当前主机、安装器和使用范围执行缺少项对应的命令。安装完成后重跑同一个检查。已有安装不在 PATH 时先定位实际 launcher；对解包不完整的 Skill，从原渠道修复。用用户自己的包管理器和可写范围安装。需要管理员权限时说明具体动作，取得授权或让用户完成该步。

| 缺少项 | Agent 的处理 |
| --- | --- |
| Python、Node 或 npx | 下载器需 Python 3.10+；当前 Hypit 需 Node.js 22.15+ 和 npm。用已有版本管理器安装兼容版本并激活，例如已有 nvm 时运行 `nvm install --lts`。npm 提供 npx。仅下载且 qiaomu 已装时无需 Node。 |
| qiaomu-download | 在用户的任务项目中运行 `npx skills add joeseesun/qiaomu-download --skill qiaomu-download -y`。沿用现有 Agent 和项目或全局范围；用户级安装才加 `-g`。首次用 npx 时可设 `npm_config_yes=true` 允许获取 skills CLI。安装后读取 `SKILL.md` 和 `references/wechat-video.md`。[上游安装说明](https://github.com/joeseesun/qiaomu-download) |
| FFmpeg、FFprobe、yt-dlp | FFmpeg 提供 ffprobe。macOS 已有 Homebrew 时只安装缺少的包，如 `brew install ffmpeg` 或 `brew install yt-dlp`；已有 uv 时也可用 `uv tool install 'yt-dlp[default]'`。Linux 可通过系统包管理器安装 ffmpeg。按所用安装器把二进制目录加入本次进程 PATH，再检查。[FFmpeg 分发](https://ffmpeg.org/download.html) · [yt-dlp 安装方式](https://github.com/yt-dlp/yt-dlp/wiki/Installation) |
| Hypit Skill | 完整拆解时运行 `npx skills add hypit-ai/hypit --skill hypit -y`，沿用当前安装范围。读取所装版本中的 `references/creation/reference-video.md`。[官方安装说明](https://github.com/hypit-ai/hypit/blob/main/docs/guide/skill.md) |
| Hypit CLI | 优先用配置或现有项目的 `node_modules/.bin/hypit`。用户级 npm 前缀可写时运行 `npm install --global @hypit/hypit`；若默认前缀需提权，可执行 `npm install --global --prefix "$HOME/.local" @hypit/hypit`，将 `~/.local/bin` 加入本次 PATH。检查 `hypit version` 与 `hypit media --help`。[Hypit 分发说明](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/environment/distribution.md) |
| 本地 Whisper | 默认识别方式。已有 uv 时可用 `uv tool install --python 3.11 openai-whisper`，有 pipx 时可用 `pipx install openai-whisper`。也可以用兼容 Python 创建用户目录内的 venv，再用该 venv 的 pip 安装 `openai-whisper`，把 `tools.whisper` 指向其 CLI。[Whisper 安装说明](https://github.com/openai/whisper#setup) |

普通依赖就绪后按[定向更新](skill-updates.md)核对本次用到的上游 Skill。没有本地微信后端连接属于媒体访问条件，按已安装的 qiaomu 下载器报告处理。首次涉及上游许可、系统信任、系统代理或向第三方转交链接时，分别遵从上游授权范围。获取模型权重可通过本地 Whisper 完成，无须付费识别账户。

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
python3 "$SKILL_DIR/scripts/user_config.py" set --mode local --local-root "$HOME/视频研究"
python3 "$SKILL_DIR/scripts/user_config.py" set --mode feishu --feishu-parent-url "$FEISHU_PARENT_URL"
python3 "$SKILL_DIR/scripts/user_config.py" set --mode both
python3 "$SKILL_DIR/scripts/user_config.py" set --mode ask
python3 "$SKILL_DIR/scripts/user_config.py" set --clear-local-root --clear-feishu-parent-url
```

`init`、`show` 和 `set` 返回 `{ok,path,config}`。从 `config.delivery` 读取保存方式和位置；`--mode ask` 让下次再问，保留已有根目录和父链接。清空本地根目录恢复建议位置，清空飞书父链接恢复「我的空间」默认目标。设置命令只合并给出的字段。提供的新飞书链接会先验证 HTTPS、官方域名与资源路径，查询串和片段会移除。认证仍由飞书 CLI 管理。

首次创建时从原 Skill 的 `config.local.json` 迁移已知工具路径、转录选择和公开来源记录。旧版明确配置的父 Wiki 链接可带入，旧样例的个人知识库名不会成为用户默认位置。原先相对于旧配置的 Skill 搜索目录会转换为绝对路径。后续只读个人配置。文件损坏时保留原文件并返回错误。需要临时指定工具配置时，向依赖检查脚本传 `--config "$CONFIG_FILE"`，该调用仅检查所给 v1/v2 文件。

| 字段 | 用法 |
| --- | --- |
| `delivery.mode` | 首次为 `null`，询问本地、飞书或两处。已选的默认方式保存为 `local`、`feishu` 或 `both`。 |
| `delivery.local_root` | 默认 `~/视频号爆款拆解`，接受绝对路径或 `~/` 开头的路径。 |
| `delivery.feishu_parent_url` | 默认 `null`。可保存 Lark 或飞书的文件夹、文档或 Wiki 节点 HTTPS 链接。 |
| `transcription.mode` | 默认 `whisper-local`，另支持明确选择的 `hypit-transcribe`。 |
| `transcription.language / threads` | 默认中文 `zh`、4 个 CPU 线程，按实际主语言和本机设置调整。 |
| `transcription.model / model_path` | 默认多语言 `small`。按绝对路径、`WHISPER_MODEL_PATH`、命名模型缓存的顺序解析；默认缓存受 `XDG_CACHE_HOME` 支持。 |
| `transcription.runtime_profile / endpoint` | Hypit 转录模式的已选 Profile 绝对路径与 endpoint 名。 |
| `tools.hypit / tools.whisper` | 选定 CLI 的绝对路径。留空时自动查找常用命令目录，Hypit 也查当前项目安装。 |
| `skill_roots` | 可选的技能根目录列表，相对路径以配置文件所在目录为准。 |
| `skill_sources` | 安装器记录不足时补充已核实的来源和范围；只记录公开来源、ref 和追踪标识。 |
