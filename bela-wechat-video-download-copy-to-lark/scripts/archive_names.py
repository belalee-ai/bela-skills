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


def archive_names(url, author_input, title_input, date_prefix=None):
    errors = []
    if not URL_PATTERN.fullmatch(url):
        errors.append("url 必须严格匹配 https://weixin.qq.com/sph/ID，不能带查询参数、片段或其他路径。")
    # Feishu titles start with the archive date as MMDD, e.g. 0902-.
    date_prefix = date_prefix or datetime.date.today().strftime("%m%d")
    if not DATE_PATTERN.fullmatch(date_prefix):
        errors.append("date 必须是四位 MMDD，月和日都补零，例如 0902。")
    author = display_text(author_input)
    title_line = next((line.strip() for line in title_input.splitlines() if line.strip()), "")
    title = display_text(title_line)
    if not author:
        errors.append("author 不能为空；请确认博主名称，不得自动推断。")
    if not title:
        errors.append("title 不能为空；请取得或确认视频标题，不得自动编造。")
    if errors:
        return {"ok": False, "status": "invalid_input", "errors": errors}

    # A deterministic suffix protects both truncation and sanitization collisions.
    identity = json.dumps([author_input, title_line], ensure_ascii=False, separators=(",", ":"))
    needs_hash = (safe_segment(author) != author_input.strip() or safe_segment(title) != title_line
                  or len((safe_segment(author) + "_" + safe_segment(title)).encode("utf-8")) > MAX_BASE_BYTES)

    def stem(joiner, title_text=title):
        value = safe_segment(author) + joiner + safe_segment(title_text)
        if needs_hash:
            suffix = "_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
            value = utf8_prefix(value, MAX_BASE_BYTES - len(suffix)) + suffix
        return value

    base = stem("_")
    return {
        "ok": True,
        "status": "archive_names_ready",
        "source_url": url,
        "author": author,
        "title": title,
        "date_prefix": date_prefix,
        # Only the folder carries the date; the three children carry a type tag.
        "directory_title": date_prefix + "-" + author + "｜" + title,
        "document_title": "【视频拆解】" + author + "｜" + title,
        "safe_base": base,
        "video_filename": "【视频】" + base + ".mp4",
        # The transcript name drops a trailing 。 so it does not read "。.md".
        "transcript_filename": "【口播稿】" + stem("｜", title.rstrip("。") or title) + ".md",
        "report_filename": base + "_视频拆解.md",
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
    parser.add_argument("--date", help="飞书标题日期前缀 MMDD，默认今天（本机日期）")
    args = parser.parse_args(argv)
    result = archive_names(args.url, args.author, args.title, args.date)
    emit(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
