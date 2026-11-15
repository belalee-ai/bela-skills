# Quality gates

Inspect the actual image at phone size and full size.

## Source fidelity

- The same hero, action, relationship, and recognizable source cues remain.
- No added person, animal, limb, prop, text, logo, or architecture that changes the event.
- Face direction, pose, hands, feet, animal anatomy, clothing, and important object geometry are coherent.
- Private UI, full URLs, QR codes, account details, and sensitive identifiers are absent or safely handled.

## Transformation quality

- The chosen style changes medium and visual organization, not just hue, contrast, or a surface filter.
- The style's one primary mechanism is obvious; multiple unrelated tricks do not compete.
- The output does not collapse into glossy 3D, generic fantasy, over-sharp HDR, or template-like AI polish.
- At phone size, one hero and one visual path are immediately legible.
- The output removes the amount of information promised by the abstraction contract. A reductive style that retains photographic inventory and microdetail fails.
- Handmade texture must show controlled irregularity; vector-perfect repetition and decorative noise both fail.

## Reduction integrity

- The maximum four recognition anchors remain traceable even when the crop or hero scale changes.
- Deleted details are genuinely unnecessary; no action, relationship, accessibility device, culturally meaningful object, or identity-critical feature disappears.
- High-change outputs use negative space as an active shape, not a blank filler or blurred extension.
- No arbitrary bird, plant, moon, lamp, window, person, vehicle, text, or decorative prop is added to make the image look artistic.

## Frame and file

- Ratio matches the confirmed choice.
- Edges are complete; no accidental crop of faces, hands, feet, signage shapes, or focal architecture.
- No stretching, squeezing, blank bands, accidental transparency, watermark, or malformed text.
- The final file opens, is saved inside the project when project-bound, and is the path recorded in `run.json`.

## Style distinction test

When generating several styles from one frame, hide their style names and check whether medium and composition grammar are distinguishable:

- `torn-paper-collage`: three to six physical fragments, one dominant fiber edge, and a source-derived overlap.
- `minimal-linocut`: one carved value mass, sparse gouge direction, and a hard two-tone structure.
- `soft-bauhaus-geometry`: four to seven pale geometric shapes on an asymmetric grid, with one real source relationship.
- `cartographic-collage`: one true route or boundary, map-like paper fields, and a small traceable scale cue.
- `risograph-collage`: two or three spot layers, visible overprint, coarse screening, and restrained misregistration.
- `matisse-cut-paper`: four to eight scissor-cut organic shapes, one active negative gap, and extreme silhouette reduction.
- `swiss-japanese-editorial`: one disciplined crop, one precise alignment accent, and 45–70% quiet paper.
- `monoprint`: one pressure-printed mass, selectively wiped light, plate tone, and at most one ghost edge.
- `sunlit-negative-space`: one small hero, one pale plane, one real shadow, extreme quiet space.
- `linear-constructive`: one assertive contour and one source-derived repeated line rhythm.
- `colorfield-landscape`: three to five spatial fields, one dominant boundary, one small scale cue.
- `poetic-ink-narrative`: sparse marks preserve an action or relationship across quiet paper.
- `earthtone-atmospheric`: selective documentary edges emerge through rubbed earth pigments and material grain.

If two outputs differ mainly by palette, surface distress, or crop while sharing the same composition grammar, at least one failed. In print styles, verify that the physical mechanism is correct: linocut uses carved removal, Riso uses separated spot layers, and monoprint uses one pressure transfer. Do not collapse all three into generic grunge.

## Acceptance and repair

- Pass: recognition-anchor fidelity, intentional reduction, style distinction, anatomy, framing, and file checks all hold.
- Local fail: use one master-lock repair for one named region.
- Structural fail: return to the selected frame and regenerate with a simpler concept.
- Persistent identity/anatomy fail: report the limitation; do not claim completion.
