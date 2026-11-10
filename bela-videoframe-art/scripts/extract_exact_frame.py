#!/usr/bin/env python3
"""Extract one full-resolution frame at an exact timestamp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _video_utils import VideoToolError, extract_frame, format_time, inspect_video, parse_time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Local video path")
    parser.add_argument("--time", required=True, help="Seconds, MM:SS.ss, or HH:MM:SS.ss")
    parser.add_argument("--output", required=True, help="PNG/JPEG output path")
    args = parser.parse_args()

    try:
        report = inspect_video(args.video)
        seconds = parse_time(args.time)
        duration = float(report["duration_seconds"])
        if seconds < 0 or seconds >= duration:
            raise VideoToolError(
                f"Requested time {seconds:.3f}s is outside the decodable range "
                f"0 <= time < {duration:.3f}s"
            )
        output = extract_frame(args.video, seconds, args.output, precise=True)
    except VideoToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "video": report["path"],
                "timestamp_seconds": round(seconds, 6),
                "timestamp": format_time(seconds),
                "output": str(Path(output).resolve()),
                "source_display_size": [report["video"]["display_width"], report["video"]["display_height"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
