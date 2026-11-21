# 按名称核对和更新依赖 Skill

下载使用 `qiaomu-download`，完整拆解还使用 `hypit`。使用前只检查本次需要的名称，来源和安装范围沿用现有安装。首次缺少时按[首次准备](setup-and-updates.md)的官方来源补装。

1. 从所选安装记录和真实目录核对名称、项目或用户范围、来源、子路径及分支或固定版本。skills CLI 通常把项目记录放在 `skills-lock.json`，用户记录放在 `~/.agents/.skill-lock.json`。只取目标条目的必要字段。
2. 比较目标 Skill 的上游内容。GitHub 来源按实际 ref 找到提交，再比该 Skill 所在目录的 Git tree SHA 与安装器对应的目录 hash。qiaomu 当前位于仓库根，Hypit 位于 `skills/hypit/`。固定 tag 或 commit 时保留用户选定的 ref。本地有定制时先保存差异，沿原管理器定向更新。
3. 已确认过期的依赖 Skill 自动定向升级。例如原来是全局安装的 Hypit，可用 `npx skills update hypit -g -y`；项目安装的 qiaomu 则在该项目运行 `npx skills update qiaomu-download -p -y`。固定版本或使用另一管理器时按原渠道操作。
4. 更新后重读实际安装路径中的 `SKILL.md` 及引用脚本，核对新标识，并重新运行本地依赖检查。新 Skill 要求某个 CLI 能力时检查实际 CLI 帮助。CLI、模型、用户 Profile 和项目产物各有自己的生命周期。
5. 无法取得上游标识时记录具体错误并说明最新状态待核验。确认过期但升级失败时保留原版本和已有工作，解决本项原因后续跑。切勿仅因更新命令返回 0 就宣称已更新。

不同发布版的 `skills check` 行为有差异；使用该命令前先确认所用实现支持真正的只读检查和名称筛选。比较已知来源的内容标识也能只读检查。记录检查日期、来源、ref、目标和结果，保留项目的锁定选择。[skills CLI](https://github.com/vercel-labs/skills) · [Hypit 定向升级](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/environment/distribution.md)
