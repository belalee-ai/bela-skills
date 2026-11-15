---
name: bela-progress-companion
description: Implement Bela character assets and motion only when a video progress overlay explicitly needs the IP character. For general progress navigation, no-IP black/white chapters, or choosing whether to add a bar, route to bela-jindutiao first. Do not assume every video needs the character.
---

# 贝拉进度条搭子

为竖屏口播制作可重复使用的贝拉小人物进度条。文字和人物运动是两个独立开关，不把上一次的模块名称、时长或站位当成新视频默认值。

2026-10-26边界更新：先由[bela-jindutiao](../bela-jindutiao/SKILL.md)判断是否需要、选择皮肤。本Skill仅处理已确认需要IP的角色资产与动作；选C黑白章节或不加IP时直接回该入口，停止下面的人物开关/角色导入流程，不能把`character=none`硬改成固定或跟随。

## 开始前

1. 在用户指定的工程中读取已有 README、AGENTS.md 与视觉规则。贝拉角色素材仅用于明确选择该角色的任务。
2. 确认唯一口播音频、实际画布、工程时长和目标剪辑环境。不能用旧视频的 5 秒测试时长替代本次时间轴。
3. 从本次要求提取两个开关：
   - `labels`: `none` 或 `chapters`
   - `character`: `fixed-left` 或 `follow-progress`
4. 用户没有明确选择且上下文不能可靠推断时，只问一个合并问题：是否显示模块文字，以及贝拉固定在左侧还是跟随进度移动。
5. 读取 [references/modes-and-inputs.md](references/modes-and-inputs.md) 生成本次最小配置。涉及实现、导出或验收时再读取 [references/render-and-qa.md](references/render-and-qa.md)。

## 固定角色资产

- 生产用 RGBA：`assets/bela-seated-dot-rgba.png`
- 已验证关节分层参考：`assets/bela-progress-rig-template.html`
- 动作参考 MP4：`assets/bela-progress-motion-reference.mp4`

模板只用于复用人物身份、遮罩、关节和动作思路。模板中的固定文字、黑底、5 秒时长、864×1824 画布和暂停网页入口都不是交付默认值。

## 核心规则

- 贝拉是进度陪伴角色，不是贴纸。即使固定在左侧，也要有手机尺寸能看清的轻动作；跟随时人物运动与进度运动必须同时可感知。
- `fixed-left` 不是贴到画布左边。必须套小红书真实发布页遮挡蒙版，人物完整轮廓向右避让；上次左上角被裁掉一半视为硬失败。
- `follow-progress` 时按人物完整轮廓控制起终点，不能只保证圆点中心在画布内。
- `labels=chapters` 时，模块名称和切换点来自真实口播语义节点或词级时间戳，不按平均时长分段；首模块文字单独避开左上角平台控件。
- `labels=none` 时删除文字与分隔线，不保留空槽；进度线和贝拉仍按选择的角色模式工作。
- 进度只前进不倒退。人物不能依赖短循环、随机值或逐帧生成；身份、右手青柠绿手环和五官保持稳定。
- 先出安全区静态定版，再出 2–5 秒可播放动作测试；两者通过后才接整条口播。用户明确要求先看图时不得提前渲染整段。
- 不以原始 HTML、代码存在、联系表或运行日志证明“动起来”；必须检查最终视频文件连续播放。
- 交付默认包含可编辑源工程、可播放预览和适配目标剪辑环境的叠加素材。只有用户明确指定 ChatCut 项目时才写入该时间线。

## 完成标准

- 本次两个开关、模块列表、时间点、画布、输出方式均有明确记录。
- 抽查最终视频的开头、模块切换、跟随路径中段、左右边界和最后一帧。
- 在小红书发布页遮挡模拟下，人物、首模块文字、脸部和手环完整可见。
- 人物动作在手机预览尺寸下看得出来，不只是整张贴图被平移。
- 字幕、口播、进度、模块切换和工程总长一致。
- 使用 `hallmark` 只做 AI 味与模板味复核；不借复核改变已经确认的结构和角色风格。
- 报告实际输出路径和状态：`静态定版待确认 / 动作测试待确认 / 本地已出片 / 已写入剪辑工程`，不把本地文件说成已发布。
