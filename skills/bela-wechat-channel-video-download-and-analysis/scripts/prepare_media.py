#!/usr/bin/env python3
"""Prepare one local archive copy. A pre-existing destination is always an error."""

import argparse
import filecmp
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path


class KeepOriginal(Exception):
    """A candidate is unsupported, larger or insufficiently faithful."""


def run(args, **kwargs):
    return subprocess.run(args, check=True, stderr=subprocess.PIPE, **kwargs)


def probe(path):
    args = ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-show_chapters", "-protocol_whitelist", "file",
            "-show_data_hash", "sha256", "-of", "json", str(path)]
    return json.loads(run(args, stdout=subprocess.PIPE).stdout)


def check_smaller(source, candidate):
    if not 0 < candidate.stat().st_size < source.stat().st_size:
        raise KeepOriginal("candidate_not_smaller")


def stream_signature(stream):
    fields = ("index", "codec_name", "codec_type", "codec_tag_string", "profile", "level",
              "width", "height", "pix_fmt", "sample_aspect_ratio", "field_order", "color_range",
              "color_space", "color_transfer", "color_primaries", "chroma_location", "time_base",
              "r_frame_rate", "avg_frame_rate", "start_pts", "duration_ts", "nb_frames",
              "sample_fmt", "sample_rate", "channels", "channel_layout", "disposition", "side_data_list")
    signature = {key: stream.get(key) for key in fields}
    signature["tags"] = {k: v for k, v in stream.get("tags", {}).items() if k != "encoder"}
    if stream["codec_type"] == "audio":
        signature["extradata_hash"] = stream.get("extradata_hash")
    return signature


def compare_records(source, candidate, directory, selector, fields):
    paths = []
    for index, item in enumerate((source, candidate)):
        path = directory / f"{selector}{index}.txt"
        with path.open("wb") as output:
            run(["ffprobe", "-v", "error", "-select_streams", selector, "-show_data_hash", "sha256",
                 "-show_entries", fields, "-of", "flat", str(item)], stdout=output)
        paths.append(path)
    if not paths[0].stat().st_size or not filecmp.cmp(*paths, shallow=False):
        raise KeepOriginal("timing_or_stream_data_changed")


def minimum_ssim(path):
    lowest = 1.0
    count = 0
    with path.open() as log:
        for line in log:
            match = re.search(r"\bAll:(\S+)", line)
            if not match or not math.isfinite(float(match[1])):
                raise KeepOriginal("invalid_ssim")
            lowest = min(lowest, float(match[1]))
            count += 1
    if not count:
        raise KeepOriginal("missing_ssim")
    return lowest


def prepare_video(source, candidate, info):
    streams = info["streams"]
    videos = [s for s in streams if s["codec_type"] == "video"]
    if len(videos) != 1 or info.get("chapters") or any(s["codec_type"] not in ("audio", "video") for s in streams):
        raise KeepOriginal("unsupported_track_layout")
    video = videos[0]
    profiles = {"Constrained Baseline": "baseline", "Main": "main", "High": "high"}
    if (video["codec_name"] != "h264" or video.get("pix_fmt") != "yuv420p"
            or video.get("profile") not in profiles or video.get("field_order") != "progressive"
            or video.get("side_data_list") or video.get("closed_captions") or video.get("film_grain")
            or video.get("color_space") not in (None, "unknown", "bt709", "smpte170m", "bt470bg")
            or video.get("color_primaries") not in (None, "unknown", "bt709", "smpte170m", "bt470bg")
            or video.get("color_transfer") not in (None, "unknown", "bt709", "smpte170m", "iec61966-2-1")
            or video.get("disposition", {}).get("attached_pic")):
        raise KeepOriginal("unsupported_video_profile_or_metadata")
    directory = candidate.parent
    run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-copyts", "-noautorotate", "-i", str(source),
         "-map", "0", "-map_metadata", "0", "-c", "copy", "-c:v", "libx264", "-preset", "slow",
         "-crf", "15", "-refs", str(video.get("refs", 1)), "-profile:v", profiles[video["profile"]], "-level:v", str(video["level"] / 10),
         "-fps_mode:v", "passthrough", "-enc_time_base:v", "demux", "-video_track_timescale",
         video["time_base"].split("/")[-1], "-avoid_negative_ts", "disabled", "-movflags", "+faststart",
         "-f", "mp4", str(candidate)])
    check_smaller(source, candidate)
    result = probe(candidate)
    if [stream_signature(s) for s in streams] != [stream_signature(s) for s in result["streams"]]:
        raise KeepOriginal("stream_parameters_changed")
    ignore = {"major_brand", "minor_version", "compatible_brands", "encoder"}
    tags = info["format"].get("tags", {})
    if any(result["format"].get("tags", {}).get(k) != v for k, v in tags.items() if k not in ignore):
        raise KeepOriginal("container_metadata_changed")
    compare_records(source, candidate, directory, "v", "frame=pts,duration:frame_side_data")
    if any(s["codec_type"] == "audio" for s in streams):
        compare_records(source, candidate, directory, "a",
                        "packet=stream_index,pts,dts,duration,flags,data_hash:packet_side_data")

    # Every frame is compared twice, including a luma edge map sensitive to small text and contours.
    graph = ("[0:v]split[x][a];[1:v]split[y][b];[x][y]ssim=f=frames.log[full];"
             "[a]extractplanes=y,sobel=scale=0.25[e];[b]extractplanes=y,sobel=scale=0.25[f];"
             "[e][f]ssim=f=edges.log[edges]")
    run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-noautorotate", "-i", str(source),
         "-noautorotate", "-i", str(candidate), "-filter_complex", graph,
         "-map", "[full]", "-map", "[edges]", "-f", "null", "-"], cwd=directory)
    scores = {"min_frame_ssim": minimum_ssim(directory / "frames.log"),
              "min_edge_ssim": minimum_ssim(directory / "edges.log")}
    if scores["min_frame_ssim"] < 0.985 or scores["min_edge_ssim"] < 0.97:
        raise KeepOriginal("quality_below_threshold " + json.dumps(scores))
    return scores


def optimize_png(source, candidate):
    # Rewrite only the compressed IDAT stream; keep palette, alpha, colour and ancillary chunks.
    data = source.read_bytes()
    offset = 8
    chunks = []
    idat = []
    while offset < len(data):
        if len(data) - offset < 12:
            raise ValueError("invalid PNG chunk")
        size, kind = struct.unpack_from(">I4s", data, offset)
        end = offset + 12 + size
        if end > len(data):
            raise ValueError("incomplete PNG chunk")
        chunk = data[offset:end]
        if zlib.crc32(chunk[4:-4]) != int.from_bytes(chunk[-4:], "big"):
            raise ValueError("invalid PNG checksum")
        chunks.append((kind, chunk))
        if kind == b"IDAT":
            idat.append(chunk[8:-4])
        offset = end
    if not idat or chunks[0][0] != b"IHDR" or chunks[-1][0] != b"IEND":
        raise ValueError("incomplete PNG")
    decoder = zlib.decompressobj()
    pixels = decoder.decompress(b"".join(idat), 128 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data:
        raise KeepOriginal("PNG_scanline_stream_outside_optimization_limits")
    packed = zlib.compress(pixels, 9)
    if len(packed) >= sum(map(len, idat)):
        raise KeepOriginal("candidate_not_smaller")
    if zlib.decompress(packed) != pixels:
        raise KeepOriginal("PNG_scanline_verification_failed")
    payload = b"IDAT" + packed
    optimized = struct.pack(">I", len(packed)) + payload + struct.pack(">I", zlib.crc32(payload))
    with candidate.open("wb") as out:
        out.write(data[:8])
        for kind, chunk in chunks:
            if kind == b"IDAT":
                out.write(optimized)
                optimized = b""
            else:
                out.write(chunk)
    return {"check": "identical_png_scanlines_and_non_IDAT_chunks"}


def image_extensions(source):
    with source.open("rb") as file:
        head = file.read(32)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return (".png",)
    if head.startswith(b"\xff\xd8\xff"):
        return (".jpg", ".jpeg")
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return (".webp",)
    if head.startswith((b"GIF87a", b"GIF89a")):
        return (".gif",)
    if head[4:8] == b"ftyp":
        if any(brand in head[8:] for brand in (b"avif", b"avis")):
            return (".avif",)
        if any(brand in head[8:] for brand in (b"heic", b"heix", b"mif1", b"msf1")):
            return (".heic", ".heif")
    raise ValueError("unrecognized image format")


def prepare_image(source, candidate, extensions):
    if source.stat().st_size > 48 * 1024 * 1024:
        raise KeepOriginal("large_image_preserved")
    if ".png" in extensions:
        return optimize_png(source, candidate)
    if not {".jpg", ".webp"}.intersection(extensions):
        raise KeepOriginal("format_preserved")
    try:
        from PIL import Image
    except ImportError:
        raise KeepOriginal("local_Pillow_unavailable")
    with Image.open(source) as original:
        if getattr(original, "n_frames", 1) != 1 or original.width * original.height > 24_000_000:
            raise KeepOriginal("large_or_multiframe_image_preserved")
        if ".jpg" in extensions:
            args = ["jpegtran", "-copy", "all", "-optimize"]
            if original.info.get("progressive") or original.info.get("progression"):
                args.append("-progressive")
            run([*args, "-outfile", str(candidate), str(source)])
        else:
            metadata = {k: original.info[k] for k in ("icc_profile", "exif", "xmp") if k in original.info}
            original.save(candidate, "WEBP", lossless=True, exact=True, method=6, **metadata)
        check_smaller(source, candidate)
        with Image.open(candidate) as changed:
            if (changed.size != original.size or changed.mode != original.mode
                    or changed.tobytes() != original.tobytes()
                    or any(original.info.get(k) != changed.info.get(k)
                           for k in ("icc_profile", "exif", "xmp", "dpi"))):
                raise KeepOriginal("image_pixel_or_metadata_difference")
    return {"check": "identical_decoded_pixels_and_color_profile"}


def prepare(kind, src, dst):
    before = src.stat()
    source_size = before.st_size
    if not src.is_file() or not source_size:
        raise ValueError("source must be a nonempty file")
    if os.path.lexists(dst):
        raise FileExistsError(f"destination already exists: {dst}")
    if kind == "video":
        info = probe(src)
        if (dst.suffix.lower() != ".mp4" or "mp4" not in info["format"]["format_name"].split(",")
                or info["format"].get("tags", {}).get("major_brand", "").strip() == "qt"
                or not any(s["codec_type"] == "video" and not s["disposition"].get("attached_pic")
                           for s in info["streams"])):
            raise ValueError("expected a downloaded MP4 video and .mp4 destination")
    else:
        info = image_extensions(src)
        if dst.suffix.lower() not in info:
            raise ValueError("destination suffix must match the actual image format: " + ", ".join(info))
    with tempfile.TemporaryDirectory(prefix=".bela-media-", dir=dst.parent) as temp:
        candidate = Path(temp) / ("candidate" + dst.suffix)
        try:
            checks = prepare_video(src, candidate, info) if kind == "video" else prepare_image(src, candidate, info)
            check_smaller(src, candidate)
            status = "compressed"
        except (KeepOriginal, FileNotFoundError, subprocess.CalledProcessError) as exc:
            reason = str(exc)
            if isinstance(exc, subprocess.CalledProcessError):
                reason = f"{exc.cmd[0]}: " + exc.stderr.decode(errors="replace").strip()[-600:]
            checks = {"reason": reason}
            shutil.copyfile(src, candidate)
            status = "original"
        after = src.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("source changed during preparation; retry with a complete download")
        # Both paths are on one filesystem; link publishes the complete file only if dst is still free.
        os.link(candidate, dst)
    return {"ok": True, "status": status, "output": str(dst), "source_bytes": source_size,
            "output_bytes": dst.stat().st_size, **checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("video", "image"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.kind, args.input.resolve(strict=True), args.output.absolute())
    except (OSError, ValueError, zlib.error, subprocess.CalledProcessError) as exc:
        result = {"ok": False, "status": "error", "reason": str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
