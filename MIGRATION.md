# 迁移清单

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
| [video-editing-workflow-bundle](https://github.com/belalee-ai/video-editing-workflow-bundle) | [`bela-video-editing`](skills/bela-video-editing/SKILL.md)、[`bela-spoken-script`](skills/bela-spoken-script/SKILL.md)、[`bela-ai-news-video`](skills/bela-ai-news-video/SKILL.md)、[`bela-text-motion-library`](skills/bela-text-motion-library/SKILL.md)、[`bela-jindutiao`](skills/bela-jindutiao/SKILL.md)、[`bela-broll`](skills/bela-broll/SKILL.md)、[`bela-ai-xhs-cover-director`](skills/bela-ai-xhs-cover-director/SKILL.md)、[`bela-ip-pic`](skills/bela-ip-pic/SKILL.md)、[`bela-motion-director`](skills/bela-motion-director/SKILL.md)、[`bela-hand-comic`](skills/bela-hand-comic/SKILL.md)、[`bela-videoframe-art`](skills/bela-videoframe-art/SKILL.md) |
| [bela-hand-comic](https://github.com/belalee-ai/bela-hand-comic) | [`bela-hand-comic`](skills/bela-hand-comic/SKILL.md) |
| [bela-videoframe-art](https://github.com/belalee-ai/bela-videoframe-art) | [`bela-videoframe-art`](skills/bela-videoframe-art/SKILL.md) |
| [bela-One-page-book](https://github.com/belalee-ai/bela-One-page-book) | [`bela-one-page-book`](skills/bela-one-page-book/SKILL.md) |
| [bela-tools](https://github.com/belalee-ai/bela-tools) | [`bela-github-publish`](skills/bela-github-publish/SKILL.md)、[`bela-skill-hygiene`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-skill-hygiene/SKILL.md)、[`bela-cart-savings-advisor`](skills/bela-cart-savings-advisor/SKILL.md) |
| [skill-hygiene](https://github.com/belalee-ai/skill-hygiene) | [`bela-skill-hygiene`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-skill-hygiene/SKILL.md) |
| [daily-job-briefing](https://github.com/belalee-ai/daily-job-briefing) | [`bela-daily-job-briefing`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-job-briefing/SKILL.md) |
| [bela-content-creator](https://github.com/belalee-ai/bela-content-creator) | [`bela-daily-briefing`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-briefing/SKILL.md)、[`bela-content-planner`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-content-planner/SKILL.md)、[`bela-video-topics`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-video-topics/SKILL.md)、[`bela-topic-picker`](skills/bela-topic-picker/SKILL.md)、[`bela-daily-job-briefing`](https://github.com/belalee-ai/bela-skills/blob/bfd7ab0b012a39d2e4b486ea1ed425ba7256dd15/skills/bela-daily-job-briefing/SKILL.md) |

本地旧名 `lidali-ai-content-editing` 对应公开版 `bela-video-editing`，`belalee-broll` 对应 `bela-broll`，`tactful-replies` 对应 `bela-tactful-replies`。

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
