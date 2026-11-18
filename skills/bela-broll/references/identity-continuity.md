# 人物身份与连续性

## 主体模式

- `P0｜无人物`：流程、数据、真实录屏、物体隐喻和纯视觉转场。人物不能增加理解时优先。
- `P1｜真人贴纸人物`：保留本次指定人物的真实脸部和照片质感，适合个人观点、经历和情绪反应。
- `P2｜动漫手绘贴纸人物`：将本次指定人物转成可辨识的手绘角色，保留参考中的面部比例和年龄感。

一条视频可以在 `P0 / P1 / P2` 之间切换，但同一人物的真人和手绘镜头共享同一份 `Character Lock`。

## Character Lock

在本条视频第一次生成人物前填写并让用户确认；后续所有人物提示词逐字复用这些字段。

```yaml
continuity_id: LOOK-01
identity: 本次指定的人物
face_anchor: 从已确认的身份参考记录脸型、眼神、年龄感和面部比例
hair_shape:
hair_color:
hair_accessory:
outfit_type:
outfit_color:
outfit_pattern:
visible_accessories:
subject_modes_allowed: [P1, P2]
style_palette:
```

## 不可变与可变

整条视频不可变：

- 脸型、发型轮廓、发色、年龄感和神态基调
- 服装类型、颜色和图案
- 发饰
- 手表、手链、耳饰等可见饰品

不同视频之间可变：

- 卫衣、衬衫、针织衫、西装、运动装等服装类型
- 与本条视频视觉风格协调的服装颜色
- 是否佩戴发饰和哪些饰品
- 真人 `P1`、手绘 `P2` 或完全无人物 `P0`

服装优先从当前风格的主色或辅助色中选，不使用无关 Logo、品牌标识和抢戏的复杂图案。

## 真人与手绘互转

同一条视频同时出现 `P1` 和 `P2` 时：

- 让发型轮廓、服装领型、袖型、主色、发饰和饰品一一对应。
- 只改变媒介语言，不改变人物造型设定。
- 真人参考负责身份，手绘校准图负责线条与角色化程度；两者发生冲突时优先保持本人脸型和神态。

## 李贝拉Bela 的人物参考

任务明确采用李贝拉Bela 的本人形象，或她的个人剪辑项目已确认沿用该人物时，读取所需的随包参考。真人照片负责确认身份，手绘校准图负责确认角色化程度。

- [真人正面惊讶](../assets/identity/lidali-front-surprised.png)
- [真人疑问姿态](../assets/identity/lidali-questioning.png)
- [真人微笑挥手](../assets/identity/lidali-smile-wave.png)
- [真人三分之二侧面指向](../assets/identity/lidali-three-quarter-point.png)
- [已确认手绘校准图](../assets/identity/lidali-anime-character-sheet.png)

使用其他人物时，采用用户提供并确认的来源。若采用作者风格，分别标明风格参考和人物参考。缺少身份参考时，先确认人物方案或选择无人物。

## 人物提示词硬约束

每次人物生成都写明：

```text
All appearances depict the same person shown in the approved identity reference.
Preserve their approved facial identity, hair silhouette, age and Character Lock.
Keep the exact same outfit, outfit color, hair accessory and visible accessories across this entire video.
Do not redesign the wardrobe between shots. Maintain the approved likeness when changing from a photo to an illustration.
```

生成后逐镜对照：脸、发型、服装、发饰、手表/手链、手部数量和动作。任一连续性项变化即不通过。
