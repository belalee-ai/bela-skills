# Generation contract

## Input roles

- `selected-frame.png`: sole edit target and source of truth for subject, action, relationships, and recognition anchors. Crop is locked only for low-change styles.
- Reality analysis object: invariant list and risk register.
- One style pack: medium and transformation grammar.
- User's ratio and intended use: output framing contract.
- Abstraction contract: deletion level, composition-change level, hero scale, and maximum four recognition anchors.

Do not pass the contact sheet as an image reference. Do not use unlicensed inspiration images as direct style inputs; translate their visual logic into the selected original style pack.

## Tool route

1. Inspect the local selected frame with the image viewer.
2. Check whether the current runtime has an image-generation or image-editing tool that accepts a local reference image.
3. In Codex, use built-in image generation in `style-transfer` edit mode when available. In Claude Code, use a configured MCP server, plugin, or API only when it supports local-reference editing.
4. If no compatible tool exists, stop before generation and deliver the selected frame plus the completed prompt scaffold. Record `generation_tool` as `null`, `generation_mode` as `prompt-only-fallback`, `final_image` as `null`, and `status` as `图片生成工具待配置`.
5. When a compatible tool exists, pass the selected local frame as the referenced image path.
6. Use one call per requested style or distinct concept.
7. Inspect the generated output before saving it into the project.
8. Use CLI/API fallback only when the user explicitly chooses that route.

## Prompt scaffold

```text
Use case: style-transfer
Asset type: art image derived from a user-selected video frame
Primary request: Translate the exact selected event with <style-id> while keeping its documentary anchors and applying deliberate reduction.
Input image: selected-frame.png is the edit target and source of truth.
Subject: <hero and relationship from reality analysis>
Recognition anchors: <maximum four cues that must remain traceable>
Must preserve: <action, direction, relationship, essential identity or object cue>
Delete: <specific clutter, surface detail, secondary objects, or background information>
May transform: <background, space, scale, surface, edge clarity, crop according to the confirmed change level>
Style/medium: <north star + medium from the selected style pack>
Composition/framing: <style-specific hero scale, negative-space target, and one primary mechanism>; composition change <low|medium|high>; output ratio <ratio>
Lighting/mood: <style-specific>
Color palette: <style-specific>
Materials/textures: <style-specific>
Constraints: One hero; no extra people or objects; no invented text, logos, signatures, or watermark; keep anatomy coherent.
Avoid: <style pack avoid list>; no generic AI polish; no unrelated scene.
```

Keep the prompt concrete and compact. Do not paste every style-file sentence into the model request.

## Abstraction and composition gate

Use one of three levels and state it in the recommendation before generation:

- `low` — lock crop, hero size, pose, and main background geometry; delete surface detail and change line/material language only.
- `medium` — preserve the event and dominant spatial relationship; allow hero repositioning, selective edge loss, and removal of secondary objects.
- `high` — preserve only the event, direction, and recognition anchors; allow the hero to become much smaller, expand negative space, or reconstruct a plausible background field. Use only after the user confirms a recommendation that explicitly says `构图改动：高`.

Do not preserve all mechanical, facial, foliage, or architectural details by default. Excess retention is a failure when the chosen style depends on reduction. Do not remove a culturally meaningful detail, accessibility device, relationship cue, or identity-critical feature merely to make the image minimal.

## Ratio gate

Ask: `这张最终图要什么比例？如果你暂时不选，我按 1:1；只有你明确确认时我才用 3:4。`

Do not infer the image ratio from a vertical or horizontal video. If the user explicitly asks for the original video ratio, use it. When reframing, prefer expansion and thoughtful crop over stretching or squeezing the source subject.

## Concept exploration

If the user asks to explore, offer at most three concepts that change the primary mechanism, such as:

- depth/repetition;
- scale/negative space;
- contour/print rhythm.

Do not present three palette swaps as three concepts. Generate only after the user selects, unless automatic mode was explicitly requested.

## Master lock repair

For a local defect, repeat:

```text
Lock: composition, crop, palette, lighting, hero position, pose, identity cues, background structure, and all already-correct regions.
Change only: <single named defect and target region>.
Do not add: people, objects, text, logos, or new stylistic effects.
```

If the defect is structural—wrong hero, lost action, unrelated place, broken overall perspective—regenerate from the selected frame instead of pretending a local repair is sufficient.

## Run record

Save a short `run.json`:

```json
{
  "source_type": "video",
  "source_video": "/absolute/path/video.mov",
  "source_image": null,
  "selected_timestamp_seconds": 7.8,
  "selected_frame": "/absolute/path/selected-frame.png",
  "style": "colorfield-landscape",
  "aspect_ratio": "1:1",
  "composition_change": "high",
  "recognition_anchors": [],
  "reality_analysis": {},
  "concept": "one sentence",
  "generation_tool": "built-in-imagegen",
  "generation_mode": "built-in-imagegen-edit",
  "final_image": "/absolute/path/art-final.png",
  "status": "最终图已验收"
}
```

For still mode, set `source_type` to `image`, set `source_video` and `selected_timestamp_seconds` to `null`, and record the preserved original in `source_image`. Private local runs may use absolute paths. Any example committed to a public repository must use relative sample paths and contain no usernames or private directory names.

When generation cannot run, keep the same record shape but use `null` for `generation_tool` and `final_image`, use `prompt-only-fallback` for `generation_mode`, and set `status` to `图片生成工具待配置`. This is a prepared handoff, not a generated result.
