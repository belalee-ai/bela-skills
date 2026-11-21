#!/usr/bin/env python3
"""Read optional credits and publication cover from the already approved Qiaomu resolver."""
import argparse
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from media_files import publish_file

MAX_IMAGE_BYTES = 24 * 1024 * 1024
IMAGE_FORMATS = {"mjpeg": "jpg", "png": "png", "webp": "webp"}
CDN_DOMAINS = ("qq.com", "qpic.cn", "gtimg.com")


def trusted_image(value):
    if not isinstance(value, str):
        return False
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        port = url.port
    except ValueError:
        return False
    return (url.scheme == "https" and url.username is None and url.password is None
            and port in (None, 443)
            and any(host == d or host.endswith("." + d) for d in CDN_DOMAINS))


class ImageRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted_image(newurl):
            raise ValueError("unrecognized image redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def save_cover(url, folder, *, opener=None):
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder) as staging_dir:
        stage = Path(staging_dir) / "cover"
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        if opener is None:
            opener = build_opener(ImageRedirect())
        with opener.open(request, timeout=20) as response:
            data = response.read(MAX_IMAGE_BYTES + 1)
        if not data or len(data) > MAX_IMAGE_BYTES:
            raise ValueError("empty or oversized cover")
        known_image = (data.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n"))
                       or (data.startswith(b"RIFF") and data[8:12] == b"WEBP"))
        if not known_image:
            raise ValueError("unsupported image header")
        stage.write_bytes(data)
        probe = subprocess.run(["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", "v:0",
                                "-show_entries", "stream=codec_name,width,height", "-of", "json",
                                str(stage)], check=True, capture_output=True, timeout=12)
        stream = json.loads(probe.stdout)["streams"][0]
        ext = IMAGE_FORMATS.get(stream["codec_name"])
        if not ext or min(stream["width"], stream["height"]) <= 1:
            raise ValueError("unusable cover format or dimensions")
        subprocess.run(["ffmpeg", "-v", "error", "-protocol_whitelist", "file,pipe", "-xerror", "-i", str(stage), "-frames:v", "1",
                        "-f", "null", "-"], check=True, capture_output=True, timeout=20)
        dest = folder / ("publication-cover." + ext)
        try:
            publish_file(stage, dest)
        except FileExistsError:
            if dest.read_bytes() != data:
                raise ValueError("a different original already exists")
        return str(dest.resolve())


def fields(feed):
    contact = feed.get("contact")
    contact = contact if isinstance(contact, dict) else {}
    author = next((v.strip() for v in (feed.get("nickname"), feed.get("nickName"),
                  feed.get("finderNickname"), contact.get("nickname"), contact.get("nickName"))
                  if isinstance(v, str) and v.strip()), "")
    title = feed.get("title") or feed.get("description")
    title = next((s.strip() for s in title.splitlines() if s.strip()), "") if isinstance(title, str) else ""
    cover = next((feed[k] for k in ("coverUrl", "cover_url", "coverImageUrl")
                  if trusted_image(feed.get(k))), None)
    return author, title, cover


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True)
    p.add_argument("--qiaomu-dir", type=Path, required=True)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--approved-resolver", required=True, choices=["upstream", "qiaomu"],
                   help="Only after user consent and a successful online download via this resolver")
    args = p.parse_args()
    if not re.fullmatch(r"https://weixin\.qq\.com/sph/[A-Za-z0-9_-]+", args.url):
        p.error("expected a single WeChat Channels share URL")
    sys.path.insert(0, str((args.qiaomu_dir / "scripts/wechat").resolve()))
    try:
        module = importlib.import_module("download_online")
        endpoint = dict(module.WORKERS)[args.approved_resolver]
        payload = module.post_profile(endpoint, args.url, 20)
        author, title, url = fields(payload["data"]["feedInfo"])
    except Exception as exc:
        print(json.dumps({"status": "metadata_unavailable", "reason": type(exc).__name__}))
        return
    result = {"author": author, "title": title, "cover_path": None}
    if url:
        try:
            result["cover_path"] = save_cover(url, args.source_dir)
        except Exception as exc:
            result["cover_error"] = type(exc).__name__
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
