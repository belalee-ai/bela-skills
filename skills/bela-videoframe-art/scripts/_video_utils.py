#!/usr/bin/env python3
"""Shared helpers for deterministic video inspection and frame extraction."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path


class VideoToolError(RuntimeError):
    pass


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise VideoToolError(f"Required executable not found: {name}")
    return path


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise VideoToolError(detail)
    return result


def parse_fraction(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        return float(numerator) / denominator_value if denominator_value else None
    return float(value)


def inspect_video(video_path: str | Path) -> dict:
    ffprobe = require_binary("ffprobe")
    video = Path(video_path).expanduser().resolve()
    if not video.is_file():
        raise VideoToolError(f"Video does not exist: {video}")

    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ]
    )
    raw = json.loads(result.stdout)
    video_streams = [stream for stream in raw.get("streams", []) if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in raw.get("streams", []) if stream.get("codec_type") == "audio"]
    if not video_streams:
        raise VideoToolError("No decodable video stream was found.")

    stream = video_streams[0]
    duration_text = stream.get("duration") or raw.get("format", {}).get("duration")
    try:
        duration = float(duration_text)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        raise VideoToolError("Video duration could not be determined.")

    rotation = 0
    tags = stream.get("tags") or {}
    if "rotate" in tags:
        try:
            rotation = int(round(float(tags["rotate"])))
        except (TypeError, ValueError):
            pass
    for side_data in stream.get("side_data_list") or []:
        if "rotation" in side_data:
            try:
                rotation = int(round(float(side_data["rotation"])))
            except (TypeError, ValueError):
                pass

    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    display_width, display_height = (height, width) if abs(rotation) % 180 == 90 else (width, height)

    return {
        "path": str(video),
        "filename": video.name,
        "duration_seconds": round(duration, 6),
        "video": {
            "codec": stream.get("codec_name"),
            "profile": stream.get("profile"),
            "coded_width": width,
            "coded_height": height,
            "display_width": display_width,
            "display_height": display_height,
            "rotation_degrees": rotation,
            "average_fps": parse_fraction(stream.get("avg_frame_rate")),
            "nominal_fps": parse_fraction(stream.get("r_frame_rate")),
            "pixel_format": stream.get("pix_fmt"),
            "color_space": stream.get("color_space"),
            "color_transfer": stream.get("color_transfer"),
            "color_primaries": stream.get("color_primaries"),
        },
        "audio_stream_count": len(audio_streams),
        "audio": [
            {
                "codec": audio.get("codec_name"),
                "sample_rate": audio.get("sample_rate"),
                "channels": audio.get("channels"),
                "channel_layout": audio.get("channel_layout"),
            }
            for audio in audio_streams
        ],
    }


def parse_time(value: str) -> float:
    value = value.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return float(value)
    parts = value.split(":")
    if len(parts) not in {2, 3}:
        raise VideoToolError(f"Unsupported time value: {value}")
    try:
        numbers = [float(part) for part in parts]
    except ValueError as exc:
        raise VideoToolError(f"Unsupported time value: {value}") from exc
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds
    hours, minutes, seconds = numbers
    return hours * 3600 + minutes * 60 + seconds


def format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remainder = seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remainder:05.2f}"
    return f"{minutes:02d}:{remainder:05.2f}"


def extract_frame(video_path: str | Path, seconds: float, output_path: str | Path, *, precise: bool) -> Path:
    ffmpeg = require_binary("ffmpeg")
    video = Path(video_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    timestamp = f"{seconds:.6f}"
    if precise:
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(video), "-ss", timestamp]
    else:
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", timestamp, "-i", str(video)]
    command.extend(["-map", "0:v:0", "-frames:v", "1", "-y", str(output)])
    run(command)
    if not output.is_file() or output.stat().st_size == 0:
        raise VideoToolError(f"Frame extraction produced no image at {format_time(seconds)}")
    return output


def quality_metrics(image_path: str | Path) -> dict:
    try:
        from PIL import Image, ImageFilter, ImageStat
    except ImportError as exc:
        raise VideoToolError("Pillow is required for candidate quality scoring.") from exc

    with Image.open(image_path) as image:
        gray = image.convert("L")
        gray.thumbnail((512, 512))
        stats = ImageStat.Stat(gray)
        mean = float(stats.mean[0])
        contrast = math.sqrt(float(stats.var[0]))
        edges = gray.filter(ImageFilter.FIND_EDGES)
        sharpness = math.sqrt(float(ImageStat.Stat(edges).var[0]))
        histogram = gray.histogram()
        total = max(1, sum(histogram))
        clipped_dark = sum(histogram[:8]) / total
        clipped_bright = sum(histogram[248:]) / total
        exposure_penalty = abs(mean - 128.0) / 128.0
        clipping_penalty = clipped_dark + clipped_bright
        score = sharpness * 1.8 + contrast * 0.45 - exposure_penalty * 18.0 - clipping_penalty * 120.0
        return {
            "score": round(score, 4),
            "brightness": round(mean, 4),
            "contrast": round(contrast, 4),
            "sharpness": round(sharpness, 4),
            "clipped_dark_ratio": round(clipped_dark, 6),
            "clipped_bright_ratio": round(clipped_bright, 6),
        }
