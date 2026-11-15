#!/usr/bin/env python3
"""Inspect a local video and emit a normalized JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _video_utils import VideoToolError, inspect_video


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Local MP4/MOV or another ffmpeg-readable video")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    try:
        report = inspect_video(args.video)
    except (VideoToolError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
