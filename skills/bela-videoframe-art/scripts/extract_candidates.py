#!/usr/bin/env python3
"""Extract temporally diverse, locally sharp candidate frames from a video."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from _video_utils import (
    VideoToolError,
    extract_frame,
    format_time,
    inspect_video,
    quality_metrics,
    require_binary,
    run,
)


def uniform_points(duration: float, count: int) -> list[float]:
    start = min(max(0.15, duration * 0.035), max(0.0, duration - 0.05))
    end = max(start, duration - max(0.15, duration * 0.035))
    if count == 1:
        return [(start + end) / 2]
    return [start + (end - start) * index / (count - 1) for index in range(count)]


def scene_points(video: str, duration: float, threshold: float) -> list[float]:
    if duration > 600:
        return []
    ffmpeg = require_binary("ffmpeg")
    filter_value = f"scale=320:-2,select='gt(scene,{threshold})',showinfo"
    result = run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            video,
            "-an",
            "-vf",
            filter_value,
            "-vsync",
            "vfr",
            "-f",
            "null",
            "-",
        ],
        check=False,
    )
    points: list[float] = []
    for match in re.finditer(r"pts_time:([0-9]+(?:\.[0-9]+)?)", result.stderr):
        value = float(match.group(1))
        if duration * 0.02 < value < duration * 0.98:
            points.append(value)
    deduped: list[float] = []
    for value in sorted(points):
        if not deduped or value - deduped[-1] >= 0.4:
            deduped.append(value)
    return deduped


def choose_scene_supplements(points: list[float], maximum: int) -> list[float]:
    if maximum <= 0 or not points:
        return []
    if len(points) <= maximum:
        return points
    return [points[round(index * (len(points) - 1) / (maximum - 1))] for index in range(maximum)] if maximum > 1 else [points[len(points) // 2]]


def thin_points(points: list[float], duration: float, count: int) -> list[float]:
    minimum_gap = max(0.35, duration / max(count * 2.4, 1))
    chosen: list[float] = []
    for point in sorted(points):
        if all(abs(point - existing) >= minimum_gap for existing in chosen):
            chosen.append(point)
    for point in uniform_points(duration, count):
        if len(chosen) >= count:
            break
        if all(abs(point - existing) >= minimum_gap * 0.7 for existing in chosen):
            chosen.append(point)
    return sorted(chosen)[:count]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Local video path")
    parser.add_argument("--output-dir", required=True, help="Directory for candidates and candidates.json")
    parser.add_argument("--count", type=int, default=12, choices=range(6, 17), metavar="6-16")
    parser.add_argument("--scene-threshold", type=float, default=0.32)
    parser.add_argument("--no-scene-detect", action="store_true", help="Skip full-video scene-change scan")
    parser.add_argument("--local-offset", type=float, default=0.14, help="Seconds sampled before/after each anchor")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"ERROR: output directory is not empty: {output_dir}", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = inspect_video(args.video)
        duration = float(report["duration_seconds"])
        uniform_count = max(4, round(args.count * 0.7))
        supplements = [] if args.no_scene_detect else choose_scene_supplements(
            scene_points(report["path"], duration, args.scene_threshold),
            args.count - uniform_count,
        )
        anchors = thin_points(uniform_points(duration, uniform_count) + supplements, duration, args.count)

        records: list[dict] = []
        with tempfile.TemporaryDirectory(prefix="bela-videoframe-art-") as temp_dir_text:
            temp_dir = Path(temp_dir_text)
            latest_safe_time = max(0.0, duration - max(0.05, args.local_offset))
            for index, anchor in enumerate(anchors, start=1):
                sample_times = sorted(
                    {
                        round(max(0.0, min(latest_safe_time, anchor + offset)), 6)
                        for offset in (-args.local_offset, 0.0, args.local_offset)
                    }
                )
                samples: list[tuple[float, Path, dict]] = []
                for sample_index, sample_time in enumerate(sample_times):
                    temp_path = temp_dir / f"anchor-{index:02d}-{sample_index}.png"
                    try:
                        extract_frame(report["path"], sample_time, temp_path, precise=False)
                    except VideoToolError:
                        continue
                    metrics = quality_metrics(temp_path)
                    samples.append((sample_time, temp_path, metrics))
                if not samples:
                    raise VideoToolError(f"No readable frame near {format_time(anchor)}")
                best_time, best_path, best_metrics = max(samples, key=lambda item: item[2]["score"])
                timestamp_slug = f"{best_time:010.3f}".replace(".", "-")
                filename = f"candidate-{index:02d}-{timestamp_slug}s.png"
                destination = output_dir / filename
                shutil.copy2(best_path, destination)
                records.append(
                    {
                        "id": f"{index:02d}",
                        "timestamp_seconds": round(best_time, 6),
                        "timestamp": format_time(best_time),
                        "file": str(destination),
                        "quality": best_metrics,
                    }
                )

        records.sort(key=lambda item: item["timestamp_seconds"])
        for index, record in enumerate(records, start=1):
            record["id"] = f"{index:02d}"
        manifest = {
            "video": report,
            "strategy": {
                "requested_count": args.count,
                "actual_count": len(records),
                "uniform_anchors": uniform_count,
                "scene_supplements": len(supplements),
                "scene_detection_skipped": args.no_scene_detect or duration > 600,
                "local_quality_offsets_seconds": [-args.local_offset, 0.0, args.local_offset],
                "note": "Automatic scores only remove obvious technical misses; a person still chooses the creative frame.",
            },
            "candidates": records,
        }
        manifest_path = output_dir / "candidates.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"manifest": str(manifest_path), "candidate_count": len(records)}, ensure_ascii=False, indent=2))
        return 0
    except (VideoToolError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
