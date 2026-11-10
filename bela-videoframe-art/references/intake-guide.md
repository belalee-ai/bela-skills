# Material intake guide

Guide first; do not make the user reverse-engineer what the Skill needs.

## First reply when no material is attached

Show the complete menu first. Keep this public numbering stable across sessions:

> 这个 Skill 目前可以生成以下 13 种风格：
>
> 01｜**撕纸解构拼贴**｜建筑强 · 风景强 · 人像中——层叠街巷、道路，以及人物处在空间中  
> 02｜**极简木刻版画**｜建筑中 · 风景中 · 人像强——轮廓鲜明的建筑、树木、人物姿态或逆光剪影  
> 03｜**柔性包豪斯几何**｜建筑强 · 风景弱 · 人像中——圆窗、拱门、立面，以及有几何服装或道具的人物  
> 04｜**地理抽象拼贴**｜建筑中 · 风景强 · 人像弱——道路、河流、海岸和建筑群的空间路线  
> 05｜**Riso 孔版叠印拼贴**｜建筑强 · 风景中 · 人像强——彩色街景、鲜明人物、活动现场与重复物体  
> 06｜**马蒂斯式剪纸色域**｜建筑弱 · 风景中 · 人像强——全身动作、植物、动物和清楚的正负形  
> 07｜**瑞日留白编辑风**｜建筑强 · 风景中 · 人像强——极简建筑、安静旅行画面、服装与克制肖像  
> 08｜**单版压印绘画**｜建筑弱 · 风景弱 · 人像强——单个人物、手部、动物、植物或孤立物体  
> 09｜**日照留白摄影**｜建筑强 · 风景中 · 人像弱——白墙、门窗、单树、树影与硬日光下的小主体  
> 10｜**当代线性构成**｜建筑强 · 风景弱 · 人像强——栏杆、格栅、车轮，以及条纹服装人物  
> 11｜**色域地景绘画**｜建筑中 · 风景强 · 人像弱——天空、水面、草坡、道路与大面积色块边界  
> 12｜**诗性水墨叙事**｜建筑弱 · 风景中 · 人像强——行走、等待、牵手、跟随和搬运等人物关系  
> 13｜**大地色氛围绘画**｜建筑强 · 风景强 · 人像中——旧建筑、乡村地景、劳动人物与风化材质  
> 14｜**不清楚，让 AI 帮我选**——上传后由 AI 推荐一个主风格和最多两个备选
>
> 如果已经知道想要哪种风格，可以直接回复：`05 + 视频` 或 `07 + 图片`。  
> 如果不确定，可以回复：`14 + 视频` 或 `14 + 图片`。

Then explain the minimum upload requirement:

> 视频尽量上传 5–60 秒的原始素材；图片尽量上传原图或干净的视频帧。好素材通常有一个清楚主角、画面不糊、主体没有被挡住，并且还能看见一点环境关系。最好不要带平台按钮、字幕、水印或聊天界面。

Ask only for the combined menu choice and upload mode. Do not ask for aspect ratio yet; ask it immediately before image generation.

Explain `强 / 中 / 弱` only when needed: `强` means the style naturally supports this subject; `中` means it works when the listed visual cue is present; `弱` means choose it only when a different property such as route, shadow, line rhythm, or material is more important than the subject category itself.

If the user already attached material, do not repeat the upload lesson. Still show the complete numbered menu once if it has not yet appeared in the conversation, then assess the material or honor the user's existing style choice.

## What to upload

### Recommended video

- Prefer original footage or a clean export, not a social-platform screen recording.
- A practical length is about 5–60 seconds. Longer videos are allowed, but ask the user to narrow the segment when the story or location changes repeatedly.
- Prefer at least one moment that stays readable for roughly half a second: limited motion blur, complete gesture, and no transition covering the subject.
- Keep the main person, animal, object, building, road, or landscape large enough to recognize.
- Preserve useful environment around the hero. A tight crop with no spatial context limits high-negative-space and color-field styles.
- Prefer clips that contain more than one subject scale: one readable close moment and one wider moment with room around the hero.
- Prefer 1080p or better when available. Lower resolution is usable only with an explicit quality warning.

### Recommended still image

- Use the original photo or a clean exported frame rather than a screenshot of an app player.
- Keep the face, body, animal, building, or terrain edge complete enough for the chosen style.
- Avoid severe blur, beauty-filter smearing, crushed shadows, blown highlights, and large text overlays.
- One clear hero is easiest. Several subjects are acceptable only when their relationship is the point of the image.

### The user does not need to do

- The user may preselect a style, but does not have to understand the terminology or choose correctly without help.
- The user does not need to trim a short video perfectly.
- The user does not need to describe every object in the scene.
- The user does not need to extract a frame if they want help choosing one.

## Fast style suitability guide

Use these cues before loading a detailed style pack:

| What is visible in the material | Primary recommendation | Why |
|---|---|---|
| Separable foreground/background, architecture, travel scene, overlapping planes | `撕纸解构拼贴` | Real depth layers can become torn fragments and partial overlaps |
| One decisive silhouette, high contrast, carved or grain-like internal direction | `极简木刻版画` | The subject survives as a two-tone mass with sparse gouge rhythm |
| Circles, arcs, bars, windows, furniture, or clean repeated geometry | `柔性包豪斯几何` | A source-derived geometric relation can organize the poster |
| Road, river, coast, path, horizon, aerial view, or journey direction | `地理抽象拼贴` | A real route or boundary can become the organizing line |
| Street scene, portrait, event, sign, architecture, or repeated group | `Riso 孔版叠印拼贴` | Strong crops can survive coarse screening and spot-color overprint |
| Clear body, gesture, plant, animal, or negative shape between subjects | `马蒂斯式剪纸色域` | The event remains readable through cut-paper silhouette and spacing |
| Architecture, object, fashion, calm portrait, or minimal travel frame | `瑞日留白编辑风` | Crop, interval, and alignment can carry the visual hierarchy |
| Portrait, hand, animal, plant, or solitary object with one strong mass | `单版压印绘画` | Uneven ink transfer and wiped light can describe one decisive form |

## Poor-fit warnings

- Do not recommend a collage style when there are no separable planes or when tearing would destroy the only identity cue.
- Do not recommend a print style when the hero has no decisive silhouette or must retain exact natural color.
- Do not recommend `地理抽象拼贴` when there is no real route, boundary, or spatial direction; never invent factual cartography.
- Do not recommend `柔性包豪斯几何` when the event depends on literal documentary context rather than shape relationships.
- Do not recommend `马蒂斯式剪纸色域` when facial detail, texture, or factual signage is the main value.
- Do not recommend `瑞日留白编辑风` for chaotic action with many equally important subjects.

## Material assessment after upload

Return a compact assessment before generation:

```text
素材判断：可用 / 有风险但可用 / 建议换一段或一帧
题材类型：建筑 / 风景 / 人像 / 混合
画面主角：<what the eye follows>
最推荐：<style> — <one source-specific reason>
题材适配：建筑强 / 风景中 / 人像中 — <one plain-language explanation>
备选：<up to two styles and their different visual logic>
构图改动：低 / 中 / 高 — <what will be deleted, enlarged, reduced, or rebuilt>
不推荐：<only styles likely to fail, with reason>
下一步：<video: show candidate sheet; still: ask the user to confirm style>
```

Avoid generic praise such as `很有氛围` or `很适合艺术化`. Point to visible evidence: face size, vanishing point, shoreline curve, facade rhythm, empty sky, repeated objects, or a complete gesture.

## Candidate recommendation after video extraction

Recommend at most three combinations:

```text
推荐 1｜07 · 00:15.05
画面：人物牵着动物沿墙行走，动作完整，墙面留白充足。
适合：诗性水墨叙事。
原因：牵引关系和行进方向在剪影中仍然成立，可以删除大部分背景而不丢事件。
构图改动：中高——人物与动物缩小，保留墙面和地面作为主要留白。
风险：人物脸较小，成图不会强调肖像身份。
```

Make each recommendation materially different. Do not list the same frame three times with three palettes unless all three media genuinely fit.
