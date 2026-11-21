#!/usr/bin/env python3
"""Resolve one share link with the installed RedFox Skill and verify its local MP4."""

import argparse
import hashlib
from http.client import HTTPException
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from archive_names import URL_PATTERN
from online_metadata import save_cover


class DownloadError(Exception):
    """Only use fixed, public status codes as messages."""


def require_public_https(value):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        raise DownloadError("invalid_media_url")
    url = urlsplit(value)
    if (url.scheme != "https" or not url.hostname or url.username is not None
            or url.password is not None or url.port not in (None, 443)):
        raise DownloadError("invalid_media_url")
    addresses = socket.getaddrinfo(url.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise DownloadError("invalid_media_url")


class MediaRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_public_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def resolve_share(url, redfox_dir):
    parser = redfox_dir / "scripts/parse_video_download.py"
    if not parser.is_file():
        raise DownloadError("missing_redfox_skill")
    if not os.environ.get("REDFOX_API_KEY"):
        raise DownloadError("missing_api_key")
    # The upstream CLI prints signed URLs in its JSON. Keep both streams in memory.
    proc = subprocess.run([sys.executable, str(parser), url], capture_output=True, timeout=45)
    if proc.returncode:
        if b"No module named 'requests'" in proc.stderr:
            raise DownloadError("missing_requests")
        raise DownloadError("resolver_failed")
    rows = json.loads(proc.stdout)
    if (not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict)
            or rows[0].get("input_url") != url):
        raise DownloadError("invalid_resolver_response")
    row = rows[0]
    if row.get("success") is not True:
        reason = str(row.get("reason", "")).lower()
        if any(term in reason for term in ("积分", "余额", "quota", "balance", "402")):
            raise DownloadError("insufficient_credit")
        if any(term in reason for term in ("401", "403", "api key", "api-key", "鉴权", "密钥")):
            raise DownloadError("authentication_failed")
        if "429" in reason or "限流" in reason:
            raise DownloadError("rate_limited")
        if "超时" in reason or "网络" in reason:
            raise DownloadError("resolver_network_error")
        raise DownloadError("resolver_failed")
    return row


def fetch_video(url, target):
    require_public_https(url)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    digest = hashlib.sha256()
    with build_opener(MediaRedirect()).open(request, timeout=60) as response:
        with target.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                output.write(chunk)
        length = response.headers.get("Content-Length")
        if length is not None and int(length) != target.stat().st_size:
            raise DownloadError("incomplete_download")
    return digest.hexdigest()


def verify_video(path):
    with path.open("rb") as media:
        if media.read(8)[4:8] != b"ftyp":
            raise DownloadError("invalid_mp4")
    proc = subprocess.run([
        "ffprobe", "-v", "error", "-protocol_whitelist", "file", "-f", "mov", "-count_frames",
        "-show_entries", "format=duration:format_tags=major_brand:"
        "stream=index,codec_name,codec_type,width,height,avg_frame_rate,nb_read_frames,nb_frames:"
        "stream_disposition=attached_pic", "-of", "json", str(path),
    ], capture_output=True)
    if proc.returncode or proc.stderr.strip():
        raise DownloadError("invalid_mp4")
    info = json.loads(proc.stdout)
    fmt = info.get("format", {})
    brand = fmt.get("tags", {}).get("major_brand", "").strip().lower()
    if brand in {"qt", "avif", "avis", "mif1", "heic", "heix", "mj2s"} or brand.startswith("3g"):
        raise DownloadError("invalid_mp4")
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), {})
    duration = float(fmt.get("duration") or 0)
    frames = int(video.get("nb_read_frames") or 0)
    if (not math.isfinite(duration) or duration <= 0 or frames < 1
            or min(video.get("width", 0), video.get("height", 0)) < 1
            or (video.get("nb_frames", "").isdigit() and frames != int(video["nb_frames"]))):
        raise DownloadError("invalid_mp4")
    return {"duration_seconds": duration, "width": video["width"], "height": video["height"],
            "frame_rate": video.get("avg_frame_rate"), "video_codec": video["codec_name"],
            "audio_codecs": [s.get("codec_name") for s in streams if s.get("codec_type") == "audio"]}


def download(url, redfox_dir, source_dir):
    if not URL_PATTERN.fullmatch(url):
        raise DownloadError("invalid_share_url")
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        raise DownloadError("missing_ffmpeg_or_ffprobe")
    source_dir.mkdir(parents=True, exist_ok=True)
    destination = source_dir / "redfox-source.mp4"
    if os.path.lexists(destination):
        raise DownloadError("destination_exists")
    row = resolve_share(url, redfox_dir)
    with tempfile.TemporaryDirectory(dir=source_dir) as stage:
        staged = Path(stage) / "video.mp4"
        digest = fetch_video(row.get("videoUrl"), staged)
        info = verify_video(staged)
        os.link(staged, destination)
        raw_text = row.get("title") if isinstance(row.get("title"), str) else ""
        lines = raw_text.splitlines()
        private_values = (row.get("videoUrl"), row.get("cover"), os.environ.get("REDFOX_API_KEY"))

        def public_line(line):
            # An echoed key or temporary link in a caption must stay out of the receipt.
            if (any(isinstance(v, str) and v and v in line for v in private_values)
                    or re.search(r"https?://\S+\?\S+", line, re.I)):
                return ""
            return line

        first = next((line.strip() for line in lines if line.strip()), "")
        result = {"ok": True, "status": "downloaded", "provider": "wechat-video-downloader", "source_url": url,
                  "video_path": str(destination.resolve()), "video_sha256": digest, "probe": info,
                  "title": public_line(first), "description_or_title": "\n".join(map(public_line, lines)),
                  "author": "", "cover_path": None}
        if row.get("cover"):
            try:
                require_public_https(row["cover"])
                cover = Path(save_cover(row["cover"], Path(stage), opener=build_opener(MediaRedirect())))
                path = source_dir / cover.name
                os.link(cover, path)
                result["cover_path"] = str(path.resolve())
            except (DownloadError, HTTPException, OSError, ValueError, subprocess.SubprocessError, LookupError):
                result["cover_status"] = "unavailable"
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--redfox-dir", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = download(args.url, args.redfox_dir, args.source_dir)
    except DownloadError as exc:
        result = {"ok": False, "status": str(exc)}
    except FileExistsError:
        result = {"ok": False, "status": "destination_exists"}
    except HTTPError as exc:
        result = {"ok": False, "status": "media_http_error", "http_status": exc.code}
    except (HTTPException, OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"ok": False, "status": "download_failed", "error_type": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
