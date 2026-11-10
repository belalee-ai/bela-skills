# 配置、安装门禁和最新版本门禁

技能是可分享的工作流，不自带其他技能、CLI、模型、红狐余额或飞书账号。第一次使用必须把依赖准备齐；配置完成后可以只发视频号链接。

## 检查顺序

1. 读取当次配置；运行 bundled `scripts/check_dependencies.py`。它只检查本地依赖，不安装、更新或下载，不宣称所有技能最新。
2. 如果任何必需项缺失、引用文件不可读、命令失败或已选模型缺失，停止整个工作流，展示缺失项、用途与用户需要执行的安装/准备。不要先下载或先建飞书目录。
3. 安装齐全后按 [技能版本检查与定向升级](skill-updates.md) 检查六个依赖技能的原始发布源。确认已安装技能过期时自动升级**指定名称和指定范围**；用户已授权该行为，无需再问。来源不明、联网失败、更新被跳过/失败不能判定为最新，应停止。
4. 重新读取新版依赖技能，重新运行本地检查，检查具体子命令/选项是否兼容。新文档需要新 CLI 时，停止请用户安装/升级 CLI；技能更新不代表运行环境也更新。
5. 依据最新 lark-shared、下载器、Hypit 说明只读验证账户访问、默认目标、所选转录服务/模型就绪，以及任何付费范围。通过后才开始业务流程。

任一阶段中断，保留 receipt 和现有文件；用户安装/修复后重跑门禁，复用已经成功的工作。严格区分依赖缺失、认证、权限、余额、目标和媒体损坏，不能对所有错误都声称“装依赖即可”。

## 配置方式

复制 `config.example.json` 为本机 `config.local.json`，或使用者提供自己的配置文件。不得把本地配置打进分发包。

```sh
python3 '<本技能目录>/scripts/check_dependencies.py' --config '<本机配置文件>'
```

示例中尖括号是要替换的说明。命令路径可含空格，应始终引用；程序调用用 argv 数组，不用拼接 shell。

| 字段 | 含义 |
| --- | --- |
| `destination.space_name` | 默认“贝拉自媒体秘密基地”，可换成其他用户自己的知识库名。 |
| `destination.node_title` | 默认“视频拆解”。没有完整路径/URL 时，在空间中递归找唯一精确匹配。 |
| `destination.node_path` | 可选完整标题数组，如 `["视频号", "视频拆解"]`，逐层查找；不是 token。 |
| `destination.parent_wiki_url` | 可选的用户自己提供的精确父节点 URL，优先于名称和路径；默认 null。 |
| `transcription.mode` | 默认 `whisper-local`；明确选择后可配置 `hypit-transcribe`。不做失败自动切换。 |
| `transcription.language` | 预计主要语种，默认 zh；以实际视频和用户指定为准。 |
| `transcription.model` | whisper-local 使用的模型名，默认 `small`。检查脚本只在 Whisper 缓存目录 `${XDG_CACHE_HOME:-~/.cache}/whisper/<model>.pt` 查找已下载文件，不下载。 |
| `transcription.model_path` | 可选，默认 null。模型不在默认缓存时才填绝对路径，或用环境变量 `WHISPER_MODEL_PATH`；优先于 `model`。 |
| `transcription.runtime_profile / endpoint` | hypit-transcribe 模式需要的已有配置文件和明确 endpoint；就绪仍要检查。 |
| `transcription.threads` | 本地识别线程数，默认 4；不据此更换模型或后端。 |
| `tools.hypit / tools.whisper` | 默认 null：自动在 PATH 中查找，找不到再查 `~/.local/bin`（pipx 默认位置）。只有命令装在这两处以外时才填绝对路径。不临时 npm exec 安装。 |
| `skill_roots` | 可选优先查找的技能根目录。默认查本技能相邻目录、项目及常见用户技能目录。 |
| `skill_sources` | 仅在原安装器不保留来源时记录经使用者确认的来源、范围、ref和追踪信息；不保存秘密。不能通过此字段把未知状态直接标记成最新。 |

`REDFOX_API_KEY` 只从下载器支持的环境/凭据机制读取，不放进配置样例或日志。默认脚本运行要求其进入当前 Python 进程环境。飞书使用各使用者自己的 `lark-cli` 登录状态；分发本技能不会传递创建者的账号权限。

## 依赖清单与用户安装要求

以下是缺失时给用户的准备依据，**不由本流程擅自执行安装**。只指出缺失的项，不要求重装已通过的组件。

| 依赖 | 作用 / 安装来源 |
| --- | --- |
| `wechat-video-downloader` skill | 红狐视频号下载流程；来源 [redfox-data/redfox-community](https://github.com/redfox-data/redfox-community)，使用仓库根目录中的准确 skill 名安装。 |
| `hypit` skill | 视频理解、时间轴与后续复刻；来源 [hypit-ai/hypit](https://github.com/hypit-ai/hypit) 的 `skills/hypit`。 |
| `lark-shared`, `lark-wiki`, `lark-drive`, `lark-doc` | 认证契约、节点解析、文件上传、docx写入与回读；来源 [飞书开放平台](https://open.feishu.cn) 的官方 skills 发布源。 |
| 技能管理 CLI `skills` | 使用已有 `skills` 或 `npx --no-install skills`；缺失时用户可通过 npm 安装 `skills`，不得去掉 no-install 偷装。 |
| Node.js、npm/npx | Hypit 和飞书 CLI 的运行/管理环境；已验证 Hypit 版本需要 Node >=22.15.0，新版本以实际包要求为准。 |
| `@hypit/hypit` CLI | 用户通过 npm 安装，或配置已有项目的真实 launcher。安装 skill 本身不会安装 CLI。 |
| `@larksuite/cli` | npm 包提供 `lark-cli`；用户按官方流程配置自己的应用、登录和权限。 |
| Python 3、`requests` | 下载器和附带辅助脚本。使用用户管理的 Python 环境安装 requests，避免向受系统管理的 Python 强装包。 |
| FFmpeg、FFprobe | 原视频探测、解码和 Hypit 网格；安装 FFmpeg 通常同时提供二者。 |
| `openai-whisper` 与本地模型 | whisper-local 模式需要现成 CLI、推理依赖及已下载的多语言模型文件；模型准备也属于前置依赖，不自动下载。 |
| Hypit WhisperX endpoint | 仅 hypit-transcribe 模式需要已配置、已运行的本地/托管服务和语言资源。按该模式当前官方文档准备。 |

安装缺失 skill 时让用户使用已安装管理器的精确 `--skill` 与 scope 参数，参考其当前帮助，不要求用户安装整个仓库所有技能。单项更新命令与只读检查陷阱见 [版本参考](skill-updates.md)。

## 分享与个人配置隔离

分发目录包含 `SKILL.md`、`agents/`、`scripts/`、`references/` 和 `config.example.json`。不包含 `config.local.json`、凭据、锁文件中的私有来源、当前任务视频/转录/日志、个人飞书 URL/token、node_modules 或机器专属启动器路径。

此自定义技能为本地作者发布版本；六个外部依赖按各自原渠道核验最新版。若以后给本技能建立发布仓库，可再记录其正式来源；没有上游时不能宣称已对本技能做过远端最新版本校验。
