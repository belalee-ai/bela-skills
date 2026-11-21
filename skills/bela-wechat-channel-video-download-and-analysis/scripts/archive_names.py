#!/usr/bin/env python3
"""Produce archive names as JSON only; never execute or create anything."""

import argparse
import datetime
import hashlib
import json
import re
import sys
import unicodedata


MAX_BASE_BYTES = 210
URL_PATTERN = re.compile(r"https://weixin\.qq\.com/sph/([A-Za-z0-9_-]+)\Z")
COVER_EXTENSIONS = frozenset(("jpg", "jpeg", "png", "webp", "gif", "avif", "heic", "heif"))
DATE_PATTERN = re.compile(r"(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])\Z")
INVALID_FILENAME_CHARACTERS = frozenset('/\\<>:"|?*')
WINDOWS_RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z", re.I)


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"ok": False, "status": "invalid_input", "errors": [message]})
        raise SystemExit(2)


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def display_text(value):
    """Remove controls from a one-line cloud title without losing its raw metadata."""
    return "".join(c for c in value if not unicodedata.category(c).startswith("C")).strip()


def safe_segment(value):
    value = unicodedata.normalize("NFC", value)
    value = "".join(
        "_" if c in INVALID_FILENAME_CHARACTERS or unicodedata.category(c).startswith("C") else c
        for c in value
    ).strip(" .")
    value = re.sub(r"_+", "_", value)
    if not value:
        value = "_"
    if WINDOWS_RESERVED.fullmatch(value):
        value = "_" + value
    return value


def utf8_prefix(value, budget):
    return value.encode("utf-8")[:budget].decode("utf-8", errors="ignore").rstrip(" .")


def archive_names(url, author_input, title_input, date_prefix=None, cover_ext=None):
    errors = []
    if not URL_PATTERN.fullmatch(url):
        errors.append("url 必须严格匹配 https://weixin.qq.com/sph/ID，不能带查询参数、片段或其他路径。")
    if date_prefix is None:
        date_prefix = datetime.date.today().strftime("%m%d")
    try:
        if not DATE_PATTERN.fullmatch(date_prefix):
            raise ValueError
        datetime.date(2000, int(date_prefix[:2]), int(date_prefix[2:]))
    except ValueError:
        errors.append("date 必须是有效月日 MMDD，例如 0902。")
    if cover_ext is not None:
        cover_ext = (cover_ext[1:] if cover_ext.startswith(".") else cover_ext).lower()
        if cover_ext not in COVER_EXTENSIONS:
            errors.append("cover-ext 必须为已核验发布封面的真实图片扩展名：" + ", ".join(sorted(COVER_EXTENSIONS)))
    author = display_text(author_input)
    title_line = next((line.strip() for line in title_input.splitlines() if line.strip()), "")
    title = display_text(title_line)
    if not author:
        errors.append("author 不能为空；请确认博主名称，不得自动推断。")
    if not title:
        errors.append("title 不能为空；请取得或确认视频标题，不得自动编造。")
    if errors:
        return {"ok": False, "status": "invalid_input", "errors": errors}

    author_segment = safe_segment(author)
    title_segment = safe_segment(title)
    identity = json.dumps([author_input, title_line], ensure_ascii=False, separators=(",", ":"))
    needs_hash = (
        author_segment != author_input.strip() or title_segment != title_line
        or "｜" in author_segment + title_segment
        or len((author_segment + "｜" + title_segment).encode("utf-8")) > MAX_BASE_BYTES
    )

    def stem(joiner, title_text=title):
        value = author_segment + joiner + (safe_segment(title_text) if title_text else "")
        if needs_hash:
            suffix = "_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
            value = utf8_prefix(value, MAX_BASE_BYTES - len(suffix)) + suffix
        return value

    base = stem("_")
    label = stem("｜")
    document_title = "【视频拆解】" + label
    return {
        "ok": True,
        "status": "archive_names_ready",
        "source_url": url,
        "author": author,
        "title": title,
        "date_prefix": date_prefix,
        "directory_title": date_prefix + "-" + label,
        "cloud_directory_title": date_prefix + "-" + author + "｜" + title,
        "cloud_document_title": "【视频拆解】" + author + "｜" + title,
        "document_title": document_title,
        "safe_base": base,
        "video_filename": "【视频】" + base + ".mp4",
        # The transcript name drops a trailing 。 so it does not read "。.md".
        "transcript_filename": "【口播稿】" + stem("｜", title.rstrip("。")) + ".md",
        "report_filename": document_title + ".md",
        "cover_filename": "【视频号封面】" + label + "." + cover_ext if cover_ext else None,
        "metadata": {
            "url_input": url,
            "author_input": author_input,
            "title_input": title_input,
            "selected_title_line": title_line,
            "filename_was_sanitized_or_shortened": needs_hash,
            "max_base_utf8_bytes": MAX_BASE_BYTES,
        },
    }


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--date", help="归档目录日期 MMDD，默认本机当天")
    parser.add_argument("--cover-ext", help="仅已核验真实发布封面时填写实际图片扩展名")
    args = parser.parse_args(argv)
    result = archive_names(args.url, args.author, args.title, args.date, args.cover_ext)
    emit(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
