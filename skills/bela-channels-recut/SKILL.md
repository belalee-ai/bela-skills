---
name: bela-channels-recut
description: "贝拉视频号剪辑（录制后）：把 Lidali 录好的口播剪成视频号成片：粗剪去停顿/重复/不吞字、按镜头表铺实拍素材、中英字幕、科技花字和音效、大人像转小圆镜。默认用 Hypit 制作，Remotion 模板兜底。用户说剪我的视频号口播、我录好了、出成片、改这条视频号时使用。录制前的写稿和镜头表交给 bela-channels-remake。独立于 lidali-ai-content-editing。"
metadata:
  version: "0.2.0"
  created: "2026-11-03"
  source_case: "1102 哈萨比斯七个 AGI 判断"
---

# 贝拉视频号剪辑

把 Lidali 录好的口播剪成视频号竖屏成片。只服务 Lidali 本人的视频号。

**上游**：`bela-channels-remake`（复刻策划）交付的口播稿和 `镜头表.md`；再往前是 `bela-wechat-video-download-copy-to-lark` 归档在飞书的参考视频和拆解。没有镜头表时（比如不是复刻，是自己的观点），先按 `bela-channels-remake` 的镜头表格式补一张再剪。
**本 Skill 的输入**：本人口播原片（由用户提供路径，如 `原视频.MOV`）+ 口播稿 + 镜头表 + `素材/`。
**交付**：工程目录内 `粗剪.mp4`、`精剪初版.mp4`、`剪辑记录.md`、`素材/来源.md`。默认不发布、不回填飞书，除非当次要求。

## 制作引擎

- **默认 Hypit**（需安装 `hypit` Skill 及同名 CLI）：口播用 Script 按说的话对齐时间（talking-head 玩法：`references/playbooks/formats/talking-head.md`），中英字幕用 `craft/captions.md`，花字/对比/名字条用项目组件（`production/component-design.md`），实拍素材用 Visual Clips，审片用 Studio。本 Skill 的硬规则作为 Brief/Treatment 里的约束写进 Hypit 工程。
- **待验证**：截至 2026-11-03，Hypit 剪本人口播 + 实拍素材这条路还没实际跑过。第一次使用先做一段 15 秒左右的代表样片（含大人像转圆镜、一个数字翻滚、一个对比、中英字幕），用户确认后再铺整片，并把结论记进复盘日志。
- **兜底 Remotion**（`template/`）：Hypit 做不到或卡住时用，1102 案例就是用它做完的。
- 付费生成（AI 画面、配音）不在默认范围；要用先讲清账号和预算，用户同意再提交。

## 硬规则（来自用户纠正，优先于一切默认）

1. **素材是视频，不是图片。** 参考视频里的 AI 静帧、照片都不算素材；放大后发糊的低清画面也不要。
2. **复用优先**：参考视频里的视频素材按它的话术位置直接复用；没有、不能用或是静帧时，自己去 YouTube（yt-dlp）/ Mixkit 找高清实拍下载，或自己做动效。采用可复用或已获得授权的素材，建立来源记录。
3. **节奏**：段落结构和段落时长跟参考视频一致（它的话术怎么推进，我们怎么推进）；同时**每 2–3 秒必须有变化**：换素材，或出现花字/标签/音效节点。前后相邻镜头不能重复同一素材。
4. **提到真人必须有本人真实视频画面**（演讲、采访、纪录片），不能用参考里认不出的人影代替。
5. **冲突点必须可视化**：数据前后对比、「最／第一／首家／唯一／快 N 倍」这类震撼说法，一定要做出能直接看到冲突的画面（数字翻滚、对比条、放大冲击+低音），不能只靠字幕。
6. **人像**：开头大人像全屏出镜，只承载第一句问候或钩子（通常 1 秒左右）；**转到下一个冲突点/下一句的那一刻**缩成画面下方居中小圆镜（不是等提到人物）；圆镜露出完整头顶并留少量空白，下到胸口；结尾放大回大人像。
7. **字幕**：中英双语，中文在上（白色得意黑），英文在下（白色斜体），无底色。只改字幕时不动口播。
8. **花字**：科技感字体（数字/英文 Orbitron，汉字粗黑体），**不加荧光发光**，字要聚焦、可读；动效按内容选，**不能全片一种**（见 [视觉系统](references/visual-system.md) 花字选型表）；每个字、每次数字跳动都配电子音效，音效压在人声下（统一增益 `SFX_GAIN`）。**花字和音效仍在多轮测试中**：新片先出 10–15 秒样片给用户看/听，确认后再铺满。
9. **口播粗剪**：1.2 倍速；删超过 0.5–0.6 秒的停顿；删重复字词、口癖、说错重说的前半句、卡壳前的半句；**绝不吞字**，每个字要说完整；原片里字本身没说完，就请用户补录，不硬拼。

## 流程

| 阶段 | 做什么 | 读 |
|---|---|---|
| 0 读入 | 读口播稿、`镜头表.md`、`素材/来源.md`；定位本人原片。镜头表缺失就先补（格式见 `bela-channels-remake/references/shot-plan.md`） | — |
| 1 粗剪 | 转写（mlx_whisper 词级）、能量包络定切点、写 keep.json、`scripts/rough_cut.py` 出 `粗剪.mp4`；**粗剪后重新转写全片**核对每个剪口 | [口播粗剪](references/editing-rules.md) |
| 2 补素材 | 镜头表里还没下载的素材按来源补齐；对方视频素材 → YouTube 真人/纪录片 → Mixkit 实拍 → 自制动效。只下需要的 10 秒 1080p 片段，入点避开片段内部切镜 | [素材来源](references/material-sourcing.md) |
| 3 对齐镜头 | 按真实粗剪重新对齐镜头表：每 2–3 秒一镜、不重复；花字、标签、章节、冲击点、中英字幕都落到真实口播的字上。Hypit 写进 Script/Source；Remotion 写进 `src/data.ts` 并跑 `scripts/check_rhythm.py` | [视觉系统](references/visual-system.md) |
| 4 渲染 | Hypit：Build + Studio 审片再导出（见 Hypit `production/builds.md`、`rendering.md`）。Remotion：`template/` 新建工程，`./render.sh` 分段渲染 | [Remotion 坑](references/remotion-pitfalls.md) |
| 5 验收 | 每 2 秒抽帧看整片；剪口附近重新转写；数字/对比段看翻滚中和落定帧；响度；把改动写进 `剪辑记录.md` | [口播粗剪 §验收](references/editing-rules.md#验收) |
| 6 复盘 | 本次用户纠正逐条记进 [复盘日志](references/review-log.md) | [复盘日志](references/review-log.md) |

Remotion 兜底时新建工程：

```bash
cp -R "<本 Skill 目录>/template" "<工程目录>/remotion"
```

在复制出的工程安装依赖并准备项目素材，见 [Remotion 配置与排错](references/remotion-pitfalls.md)。[案例时间轴数据](examples/1102-哈萨比斯-data.ts)用于理解数据结构，所引用的项目原片和素材由使用者准备。

## 交付说明

报告时分开写：已渲染 / 已抽帧检查 / 已转写核对剪口 / **未实际回听** / 未逐帧合规 / 未发布 / 飞书未回填。没听过就不说听感没问题。

## 自我进化

每次使用后把用户的纠正、新做法记进 `references/review-log.md`。每日复盘（自动任务或手动）：读当天用到本 Skill 的对话，挑出**最常出现、最需要解决的 3 个问题**，提出对本 Skill 的修改，用户确认后再改正文，并在 `metadata.version` 和日志里记录。
