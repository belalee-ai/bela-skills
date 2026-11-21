#!/usr/bin/env python3
"""Manage personal delivery preferences for the WeChat Channels analysis skill."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib.parse import urlsplit, urlunsplit


SKILL_DIRECTORY = Path(__file__).resolve().parent.parent
NAME = "bela-wechat-channel-video-download-and-analysis"
OLD_NAME = "bela-wechat-video-download-copy-to-lark"
DEFAULT_ROOT = "~/视频号爆款拆解"
MODES = ("local", "feishu", "both")


def config_path():
    return Path.home() / ".bela-skills-config" / (NAME + ".config")


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"配置文件不是有效的 UTF-8 JSON，请修复原文件：{path}") from error
    if not isinstance(data, dict):
        raise ValueError(f"配置文件须为 JSON 对象：{path}")
    if type(data.get("schema_version")) is not int or data["schema_version"] not in (1, 2):
        raise ValueError(f"配置文件的 schema_version 应为 1 或 2：{path}")
    return data


def feishu_url(value):
    if value is None:
        return None
    message = "请提供飞书或 Lark 的 HTTPS 文档、文件夹或知识库节点链接"
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError(message)
    try:
        url = urlsplit(value)
        host = url.hostname or ""
        port = url.port
    except ValueError as error:
        raise ValueError(message) from error
    valid_host = re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*(?:feishu\.cn|larksuite\.com)", host)
    valid_path = re.fullmatch(r"/(?:wiki|docx?|docs|(?:drive|space)/folder|folder)/[A-Za-z0-9_-]+/?", url.path)
    if (url.scheme != "https" or not valid_host or not valid_path or url.username is not None
            or url.password is not None or port not in (None, 443)):
        raise ValueError(message)
    return urlunsplit(("https", host, url.path.rstrip("/"), "", ""))


def local_root(value):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError("本地根目录须为绝对路径或 ~/ 开头的路径")
    if value == "~" or value.startswith("~/") or Path(value).is_absolute():
        return value
    raise ValueError("本地根目录须为绝对路径或 ~/ 开头的路径")


def clean_delivery(data, preserve_unknown=True):
    if not isinstance(data, dict):
        raise ValueError("delivery 应为含保存方式和位置的 JSON 对象")
    mode = data.get("mode")
    if mode is not None and mode not in MODES:
        raise ValueError("delivery.mode 应为 null、local、feishu 或 both")
    delivery = dict(data) if preserve_unknown else {}
    delivery.update(mode=mode, local_root=local_root(data.get("local_root", DEFAULT_ROOT)),
                    feishu_parent_url=feishu_url(data.get("feishu_parent_url")))
    return delivery


def legacy_path():
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME") or home / ".codex").expanduser()
    candidates = [SKILL_DIRECTORY / "config.local.json"]
    for root in (SKILL_DIRECTORY.parent, home / ".agents/skills", codex_home / "skills", home / ".claude/skills"):
        candidates.extend(root / name / "config.local.json" for name in (NAME, OLD_NAME))
    return next((path for path in candidates if path.is_file()), None)


def public_sources(sources):
    """Only import public repository identifiers, scope, refs and content tracking fields."""
    if not isinstance(sources, dict):
        raise ValueError("skill_sources 应为 JSON 对象")
    result = {}
    for skill, info in sources.items():
        if skill not in ("qiaomu-download", "hypit"):
            continue
        fields = info if isinstance(info, dict) else {"source": info}
        entry = {}
        for key, value in fields.items():
            if not isinstance(value, str) or not value:
                continue
            if key in ("source", "repository", "repo", "url", "sourceUrl", "source_url"):
                if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
                    entry[key] = value
                else:
                    parsed = urlsplit(value)
                    if (parsed.scheme == "https" and parsed.hostname == "github.com" and
                            re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", parsed.path)):
                        entry[key] = "https://github.com" + parsed.path
            elif key in ("scope", "sourceType", "ref", "skillPath", "skill_path", "path",
                         "hash", "digest", "commit", "skillFolderHash", "computedHash"):
                if re.fullmatch(r"[A-Za-z0-9._/@+-]+", value):
                    entry[key] = value
        if entry:
            result[skill] = entry if isinstance(info, dict) else entry["source"]
    return result


def migrated_config(data, previous):
    final = read_json(SKILL_DIRECTORY / "config.example.json")
    for section in ("transcription", "tools"):
        values = data.get(section, {})
        if not isinstance(values, dict):
            raise ValueError(f"{section} 应为 JSON 对象：{previous}")
        for key in final[section]:
            if key not in values or values[key] is None:
                continue
            value = values[key]
            if key == "threads":
                valid = type(value) is int and value > 0
            elif key in ("hypit", "whisper", "model_path", "runtime_profile"):
                valid = isinstance(value, str) and (Path(value).is_absolute() or value.startswith("~/"))
            elif key == "mode":
                valid = value in ("whisper-local", "hypit-transcribe")
            else:
                valid = isinstance(value, str) and re.fullmatch(r"[\w.-]+", value, re.UNICODE)
            if not valid:
                raise ValueError(f"原配置中的 {section}.{key} 格式有误，请检查原文件：{previous}")
            final[section][key] = value
    roots = data.get("skill_roots", [])
    if not isinstance(roots, list) or any(not isinstance(x, str) or not x.strip() for x in roots):
        raise ValueError("skill_roots 应为路径字符串数组")
    if any("://" in item or any(ord(c) < 32 for c in item) for item in roots):
        raise ValueError("skill_roots 只能包含文件系统目录")
    final["skill_roots"] = [str((previous.parent / Path(item).expanduser()).resolve()) for item in roots]
    final["skill_sources"] = public_sources(data.get("skill_sources", {}))
    explicit = data.get("destination")
    if "delivery" in data:
        final["delivery"] = clean_delivery(data["delivery"], preserve_unknown=False)
    elif isinstance(explicit, dict) and explicit.get("parent_wiki_url"):
        final["delivery"]["feishu_parent_url"] = feishu_url(explicit["parent_wiki_url"])
    return final


@contextmanager
def settings_lock(directory):
    if directory.is_symlink():
        raise ValueError("个人配置目录需为真实目录")
    directory.mkdir(mode=0o700, exist_ok=True)
    lock_path = directory / ("." + NAME + ".lock")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(lock_path, flags, 0o600), "r+b") as handle:
        if os.name == "nt":
            import msvcrt
            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def write_atomic(path, data):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix="." + NAME + "-", delete=False) as handle:
        temp_path = Path(handle.name)
        try:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            handle.close()
            temp_path.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def preferences(changes=None):
    path = config_path()
    with settings_lock(path.parent):
        if path.is_symlink():
            raise ValueError("个人配置文件需为真实文件")
        if path.exists():
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("个人配置路径需为普通文件")
            original = read_json(path)
            data = migrated_config(original, path) if original["schema_version"] == 1 else original.copy()
            path.chmod(0o600)
        else:
            original = None
            old = legacy_path()
            data = migrated_config(read_json(old), old) if old else read_json(SKILL_DIRECTORY / "config.example.json")
        delivery = clean_delivery(data.get("delivery", {}))
        delivery.update(changes or {})
        data["delivery"] = clean_delivery(delivery)
        if data != original:
            write_atomic(path, data)
        return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("show")
    update = commands.add_parser("set")
    update.add_argument("--mode", choices=(*MODES, "ask"))
    local = update.add_mutually_exclusive_group()
    local.add_argument("--local-root")
    local.add_argument("--clear-local-root", action="store_true")
    remote = update.add_mutually_exclusive_group()
    remote.add_argument("--feishu-parent-url")
    remote.add_argument("--clear-feishu-parent-url", action="store_true")
    args = parser.parse_args()
    changes = {}
    if args.command == "set":
        if args.mode is not None:
            changes["mode"] = None if args.mode == "ask" else args.mode
        if args.local_root is not None or args.clear_local_root:
            changes["local_root"] = DEFAULT_ROOT if args.clear_local_root else args.local_root
        if args.feishu_parent_url is not None or args.clear_feishu_parent_url:
            changes["feishu_parent_url"] = args.feishu_parent_url
        if not changes:
            parser.error("set 至少须指定一项保存偏好")
    try:
        data = preferences(changes)
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "path": str(config_path()), "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "path": str(config_path()), "config": data}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
