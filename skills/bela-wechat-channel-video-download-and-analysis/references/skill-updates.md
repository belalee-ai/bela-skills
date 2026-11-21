# 按名称核对和更新依赖 Skill

本地入口已能执行时直接处理本次作品。首次缺少所选依赖时，按[首次准备](setup-and-updates.md)补装；实跑遇到版本不兼容或用户要求核对、更新时再执行以下步骤。下载只涉及选定的 `qiaomu-download` 或 `wechat-video-downloader`，完整拆解另用 `hypit`。沿用已核实的来源和安装范围。

1. 从所选安装记录和真实目录核对名称、项目或用户范围、来源、子路径及分支或固定版本。skills CLI 通常把项目记录放在 `skills-lock.json`，用户记录放在 `~/.agents/.skill-lock.json`。只取目标条目的必要字段。
2. 找到上游中对应的 Skill 目录。乔木在仓库根，红狐在 `skills/wechat-video-downloader/`，Hypit 在 `skills/hypit/`。如有上次安装的 commit，比较旧提交和追踪 ref 中该目录各自的 Git tree SHA。只有安装器内容哈希时，按安装器相同算法比较文件。保留固定 tag 或 commit，本地有定制时先保存差异。[红狐官方目录](https://github.com/redfox-data/redfox-community/tree/main/skills/wechat-video-downloader)
3. 确认所选下载器过期后，沿原渠道定向升级。在原项目目录运行 `npx skills update "$DOWNLOAD_PROVIDER" -p -y`，其中 `DOWNLOAD_PROVIDER` 为本次选定的名称。原为用户级安装时用 `-g`。例如完整拆解另需更新用户级 Hypit 时，可用 `npx skills update hypit -g -y`。
4. 更新后重读实际安装路径中的 `SKILL.md` 及引用脚本，核对新标识，并按同一下载器和任务模式重新运行本地依赖检查。新 Skill 要求某个 CLI 能力时检查实际 CLI 帮助。CLI、模型、用户 Profile 和项目产物各有自己的生命周期。
5. 无法取得上游标识时记录具体错误并说明最新状态待核验。确认过期但升级失败时保留原版本和已有工作，解决本项原因后续跑。切勿仅因更新命令返回 0 就宣称已更新。

不同发布版的 `skills check` 行为有差异；使用该命令前先确认所用实现支持真正的只读检查和名称筛选。比较已知来源的内容标识也能只读检查。记录检查日期、来源、ref、目标和结果，保留项目的锁定选择。[skills CLI](https://github.com/vercel-labs/skills) · [Hypit 定向升级](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/environment/distribution.md)
