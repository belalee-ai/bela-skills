#!/usr/bin/env python3
"""Build a numbered contact sheet from extract_candidates.py output."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Path to candidates.json")
    parser.add_argument("--output", required=True, help="Contact sheet image path")
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--cell-width", type=int, default=520)
    args = parser.parse_args()

    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError:
        print("ERROR: Pillow is required to build the contact sheet.", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest).expanduser().resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        candidates = manifest["candidates"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: invalid manifest: {exc}", file=sys.stderr)
        return 2
    if not candidates:
        print("ERROR: manifest has no candidates", file=sys.stderr)
        return 2

    columns = max(1, args.columns)
    cell_width = max(240, args.cell_width)
    display_width = int(manifest.get("video", {}).get("video", {}).get("display_width") or 16)
    display_height = int(manifest.get("video", {}).get("video", {}).get("display_height") or 9)
    source_ratio = display_height / max(1, display_width)
    image_height = round(cell_width * min(max(source_ratio, 0.60), 1.60))
    label_height = 54
    gap = 20
    margin = 28
    rows = math.ceil(len(candidates) / columns)
    sheet_width = margin * 2 + columns * cell_width + (columns - 1) * gap
    sheet_height = margin * 2 + rows * (image_height + label_height) + (rows - 1) * gap
    sheet = Image.new("RGB", (sheet_width, sheet_height), "#F5F2EA")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:
        # Pillow < 10.1 does not accept the size keyword. Keep the contact
        # sheet usable instead of failing on otherwise supported installs.
        font = ImageFont.load_default()

    for item_index, item in enumerate(candidates):
        row, column = divmod(item_index, columns)
        left = margin + column * (cell_width + gap)
        top = margin + row * (image_height + label_height + gap)
        image_path = Path(item["file"])
        if not image_path.is_absolute():
            image_path = manifest_path.parent / image_path
        try:
            with Image.open(image_path) as source:
                fitted = ImageOps.contain(source.convert("RGB"), (cell_width, image_height), method=Image.Resampling.LANCZOS)
        except OSError as exc:
            print(f"ERROR: cannot read candidate {image_path}: {exc}", file=sys.stderr)
            return 2
        frame = Image.new("RGB", (cell_width, image_height), "#D8D4CA")
        paste_left = (cell_width - fitted.width) // 2
        paste_top = (image_height - fitted.height) // 2
        frame.paste(fitted, (paste_left, paste_top))
        sheet.paste(frame, (left, top))
        draw.rectangle((left, top + image_height, left + cell_width, top + image_height + label_height), fill="#151515")
        label = f"{item['id']}   {item['timestamp']}"
        draw.text((left + 16, top + image_height + 13), label, fill="white", font=font)

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=94)
    print(json.dumps({"output": str(output), "size": [sheet_width, sheet_height], "count": len(candidates)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
