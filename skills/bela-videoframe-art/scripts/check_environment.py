#!/usr/bin/env python3
"""Check local dependencies used by the deterministic video workflow."""

from __future__ import annotations

import json
import shutil
import sys


def version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in value.split("."):
        digits = "".join(character for character in part if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def main() -> int:
    checks: dict[str, object] = {
        "python": {
            "version": ".".join(str(part) for part in sys.version_info[:3]),
            "minimum": "3.9",
            "ok": sys.version_info >= (3, 9),
        },
        "ffmpeg": {"path": shutil.which("ffmpeg")},
        "ffprobe": {"path": shutil.which("ffprobe")},
    }

    try:
        import PIL

        pillow_version = getattr(PIL, "__version__", "unknown")
        pillow_ok = pillow_version == "unknown" or version_tuple(pillow_version) >= (9, 0)
        checks["pillow"] = {
            "version": pillow_version,
            "minimum": "9.0",
            "ok": pillow_ok,
        }
    except ImportError:
        checks["pillow"] = {"version": None, "minimum": "9.0", "ok": False}

    checks["ffmpeg"]["ok"] = bool(checks["ffmpeg"]["path"])
    checks["ffprobe"]["ok"] = bool(checks["ffprobe"]["path"])
    ok = all(bool(item.get("ok")) for item in checks.values() if isinstance(item, dict))
    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    if not ok:
        print(
            "Install Python 3.9+, ffmpeg/ffprobe, and Pillow 9.0+ before video mode.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
