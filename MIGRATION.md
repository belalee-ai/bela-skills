# 迁移清单

## 视频号下载与拆解改名

`bela-wechat-video-download-copy-to-lark` 已改名为 [`bela-wechat-channel-video-download-and-analysis`](skills/bela-wechat-channel-video-download-and-analysis/SKILL.md)。更新按名称调用的命令、工作流和本机 Skill 引用。项目级安装命令如下。

```bash
npx skills add belalee-ai/bela-skills --skill bela-wechat-channel-video-download-and-analysis
```

首次使用时选择本地、飞书或两处，之后可复用保存偏好。本地默认在 `~/视频号爆款拆解/` 按视频建目录，交付视频、口播稿和带图 Markdown 拆解报告。选择飞书或两处时，作品目录建在用户给出的飞书文件夹或知识库父节点下。旧配置中父链接为空时，下次飞书归档会先请你粘贴链接；已经指定过的位置可以继续沿用。保存偏好记录在 `~/.bela-skills-config/bela-wechat-channel-video-download-and-analysis.config`。更换设备或账号后，先确认登录身份与父位置再归档。

旧配置没有 `download.provider` 时，下次下载会先推荐红狐，也可选乔木。确认后记住选择，之后直接沿用。上一版使用乔木的用户可继续选乔木。选红狐时，在本机为运行脚本的环境配置自己的 `REDFOX_API_KEY`。也可以说「仅这次用红狐」临时覆盖，或「忘记下载器」恢复下次询问。[下载器安装与配置](skills/bela-wechat-channel-video-download-and-analysis/references/setup-and-updates.md)

## 2026-11-15：统一合集目录

现有 26 个 Skill 从根目录移到 `skills/<name>/`，名称、功能与随包资源保留。合集和单项安装仍使用：

```bash
npx skills add belalee-ai/bela-skills
npx skills add belalee-ai/bela-skills --skill bela-spoken-script
```

引用本仓库旧根目录的文件直链需要增加 `skills/`，例如 `bela-spoken-script/SKILL.md` 改为 `skills/bela-spoken-script/SKILL.md`。Skill 名称不变，按名称安装无需改命令；不保留重复技能目录。

## 旧仓库来源

从这些已发布仓库迁入 Skill。历史提交和旧版安装入口保留。第三方依赖沿用原来源。

| 旧仓库 | 合集入口 |
| --- | --- |
| [video-editing-workflow-bundle](https://github.com/belalee-ai/video-editing-workflow-bundle) | [`bela-video-editing`](https://github.com/belalee-ai/bela-skills/blob/3fc7a8184e974c70a61755e72c21d39d6c89321d/skills/bela-video-editing/SKILL.md)、[`bela-spoken-script`](skills/bela-spoken-script/SKILL.md)、[`bela-ai-news-video`](https://github.com/belalee-ai/bela-skills/blob/0edc4c40474d8d384965b6ccd59a1b0560d52d1d/skills/bela-ai-news-video/SKILL.md)、[`bela-text-motion-library`](skills/bela-text-motion-library/SKILL.md)、[`bela-jindutiao`](skills/bela-jindutiao/SKILL.md)、[`bela-broll`](skills/bela-broll/SKILL.md)、[`bela-ai-xhs-cover-director`](skills/bela-ai-xhs-cover-director/SKILL.md)、[`bela-ip-pic`](skills/bela-ip-pic/SKILL.md)、[`bela-motion-director`](skills/bela-motion-director/SKILL.md)、[`bela-hand-comic`](skills/bela-hand-comic/SKILL.md)、[`bela-videoframe-art`](skills/bela-videoframe-art/SKILL.md) |
| [bela-hand-comic](https://github.com/belalee-ai/bela-hand-comic) | [`bela-hand-comic`](skills/bela-hand-comic/SKILL.md) |
| [bela-videoframe-art](https://github.com/belalee-ai/bela-videoframe-art) | [`bela-videoframe-art`](skills/bela-videoframe-art/SKILL.md) |
| [bela-One-page-book](https://github.com/belalee-ai/bela-One-page-book) | [`bela-one-page-book`](skills/bela-one-page-book/SKILL.md) |
| [bela-tools](https://github.com/belalee-ai/bela-tools) | [`bela-github-publish`](skills/bela-github-publish/SKILL.md)、[`bela-skill-hygiene`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-skill-hygiene/SKILL.md)、[`bela-cart-savings-advisor`](skills/bela-cart-savings-advisor/SKILL.md) |
| [skill-hygiene](https://github.com/belalee-ai/skill-hygiene) | [`bela-skill-hygiene`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-skill-hygiene/SKILL.md) |
| [daily-job-briefing](https://github.com/belalee-ai/daily-job-briefing) | [`bela-daily-job-briefing`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-job-briefing/SKILL.md) |
| [bela-content-creator](https://github.com/belalee-ai/bela-content-creator) | [`bela-daily-briefing`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-briefing/SKILL.md)、[`bela-content-planner`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-content-planner/SKILL.md)、[`bela-video-topics`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-video-topics/SKILL.md)、[`bela-topic-picker`](skills/bela-topic-picker/SKILL.md)、[`bela-daily-job-briefing`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-job-briefing/SKILL.md) |

本地旧名 `lidali-ai-content-editing` 已改名为 `bela-video-editing`，作为作者个人版另行维护，不在本合集发布；合集中原有的通用版已移除，上表链接指向移除前的版本。`belalee-broll` 的人物与风格参考及制作流程已合并到 [`bela-broll`](skills/bela-broll/SKILL.md)，`tactful-replies` 对应 `bela-tactful-replies`。

本地旧名 `ameng-tiny-png` 对应 [`bela-tiny-png`](skills/bela-tiny-png/SKILL.md)。

本地使用的上游 `draw-your-font` 对应合集适配版 [`bela-draw-your-font`](skills/bela-draw-your-font/SKILL.md)。CLI 继续使用上游 npm 包，适配版随附原 MIT 许可。

## 视频号剪辑与角色素材

三个原本只在作者本机安装的 Skill 已加入合集，可按需安装：

```bash
npx skills add belalee-ai/bela-skills --skill bela-channels-recut --skill bela-progress-companion --skill bela-wechat-cover
```

## 历史版本

2026-11-18，以下 Skill 从合集的当前安装列表下架。完整文件可从下架前的提交取回。

- [内容规划 · bela-content-planner](https://github.com/belalee-ai/bela-skills/tree/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-content-planner)
- [视频选题草案 · bela-video-topics](https://github.com/belalee-ai/bela-skills/tree/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-video-topics)
- [Skill 体检 · bela-skill-hygiene](https://github.com/belalee-ai/bela-skills/tree/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-skill-hygiene)
- [职位日报 · bela-daily-job-briefing](https://github.com/belalee-ai/bela-skills/tree/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-job-briefing)
- [AI 日报 · bela-daily-briefing](https://github.com/belalee-ai/bela-skills/tree/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-briefing)

2026-11-18，AI 新闻视频 Skill 从当前安装列表下架。[历史版本](https://github.com/belalee-ai/bela-skills/tree/0edc4c40474d8d384965b6ccd59a1b0560d52d1d/skills/bela-ai-news-video)可用于恢复。
