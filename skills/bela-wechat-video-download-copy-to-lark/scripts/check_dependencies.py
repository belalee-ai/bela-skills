#!/usr/bin/env python3
"""Read-only local dependency gate. Does not install, update, authenticate or download."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


SKILL_DIRECTORY = Path(__file__).resolve().parent.parent
CORE_FILES = {
    "wechat-video-downloader": (
        "references/core_workflow.md", "scripts/parse_video_download.py",
    ),
    "hypit": (
        "references/creation/reference-video.md", "references/creation/project-files.md",
        "references/environment/distribution.md", "references/environment/local-tools.md",
        "references/environment/model-and-provider.md",
    ),
    "lark-shared": (
        "references/lark-shared-identity-and-permissions.md",
        "references/lark-shared-output-contract.md", "references/lark-wiki-token-routing.md",
    ),
    "lark-wiki": (
        "references/lark-wiki-node-get.md", "references/lark-wiki-node-create.md",
        "references/lark-wiki-node-list.md", "references/lark-wiki-move.md",
    ),
    "lark-drive": ("references/lark-drive-upload.md", "references/lark-drive-import.md"),
    "lark-doc": (
        "references/lark-doc-create.md", "references/lark-doc-create-workflow.md",
        "references/lark-doc-md.md", "references/lark-doc-fetch.md",
    ),
}
COMMANDS = {
    "python3": ["--version"], "node": ["--version"], "npm": ["--version"],
    "npx": ["--version"], "lark-cli": ["--version"], "hypit": ["version"],
    "ffmpeg": ["-version"], "ffprobe": ["-version"],
}
WHISPER_REQUIRED_FLAGS = (
    "--model", "--word_timestamps", "--language", "--device", "--fp16",
    "--threads", "--output_format", "--output_dir",
)


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"ok": False, "status": "local_dependencies_blocked", "missing_dependencies": [
            {"dependency": "arguments", "reason": message}
        ], "next_action": "修正参数后重新运行检查。"})
        raise SystemExit(2)


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def readable_file(path, nonempty=True):
    try:
        if not path.is_file() or (nonempty and path.stat().st_size == 0):
            return False
        with path.open("rb") as handle:
            handle.read(1)
        return True
    except (OSError, ValueError):
        return False


def absolute_existing_file(value):
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() and readable_file(path) else None


def frontmatter_name(path):
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.fullmatch(r"name:\s*(.*?)\s*", line)
        if match:
            value = match.group(1)
            if value.startswith(('"', "'")):
                quote = value[0]
                end = value.find(quote, 1)
                return value[1:end] if end > 0 else None
            return value.split(" #", 1)[0].strip()
    return None


def command_environment():
    env = os.environ.copy()
    env.update({
        "npm_config_offline": "true", "NPM_CONFIG_OFFLINE": "true",
        "npm_config_yes": "false", "npm_config_update_notifier": "false",
        "NO_UPDATE_NOTIFIER": "1", "CI": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    # Neither a local version check nor a Python import needs this secret.
    env.pop("REDFOX_API_KEY", None)
    return env


def run_local(argv, timeout):
    """Never run a shell; never expose unfiltered child output in JSON."""
    try:
        completed = subprocess.run(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
            check=False, shell=False, env=command_environment(),
        )
    except subprocess.TimeoutExpired:
        return False, "", "本地命令检查超时"
    except OSError:
        return False, "", "本地命令无法启动"
    output = completed.stdout + "\n" + completed.stderr
    if completed.returncode != 0:
        return False, output, "本地命令退出码为 " + str(completed.returncode)
    if not output.strip():
        return False, output, "本地命令没有返回版本或帮助信息"
    return True, output, None


def resolve_tool(name, override=None):
    if override is not None:
        if not isinstance(override, str):
            return None, "配置必须是绝对启动器路径或 null"
        path = Path(override).expanduser()
        if not path.is_absolute():
            return None, "配置的启动器必须使用绝对路径"
        if not readable_file(path) or not os.access(path, os.X_OK):
            return None, "配置的启动器不存在、为空、不可读或不可执行"
        return str(path), None
    path = shutil.which(name)
    if path:
        return path, None
    # pipx/uv tool installs land here, but GUI-launched shells often omit it from PATH.
    user_bin = Path.home() / ".local" / "bin" / name
    if readable_file(user_bin) and os.access(user_bin, os.X_OK):
        return str(user_bin), None
    return None, "PATH 和 ~/.local/bin 中都没有已安装的命令"


def whisper_cache_directory():
    cache_root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache_root).expanduser() / "whisper"


def resolve_whisper_model(transcription):
    """Explicit path wins; otherwise look up the named model in Whisper's default cache. Never downloads."""
    explicit = transcription.get("model_path") or os.environ.get("WHISPER_MODEL_PATH")
    if explicit:
        model = absolute_existing_file(explicit)
        return model, None if model else "model_path / WHISPER_MODEL_PATH 指向的文件不存在、为空或不是绝对路径"
    name = transcription.get("model")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        return None, "需要 transcription.model（如 small）或 model_path"
    candidate = whisper_cache_directory() / (name + ".pt")
    if readable_file(candidate):
        return candidate, None
    return None, "Whisper 缓存中没有已下载的模型文件：" + str(candidate)


def destination_error(destination):
    """Validate local routing inputs only; do not resolve any remote Wiki object."""
    if not isinstance(destination, dict):
        return "destination 必须是 JSON 对象；请配置归档目标"
    wiki_url = destination.get("parent_wiki_url")
    if wiki_url is not None and not isinstance(wiki_url, str):
        return "destination.parent_wiki_url 必须是 HTTPS Wiki URL 字符串或 null"
    if isinstance(wiki_url, str) and wiki_url.strip():
        try:
            parsed = urlsplit(wiki_url.strip())
            valid = (
                parsed.scheme == "https" and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and not any(c.isspace() for c in wiki_url.strip())
                and re.fullmatch(r"/wiki/[A-Za-z0-9]+", parsed.path) is not None
            )
        except ValueError:
            valid = False
        return None if valid else "parent_wiki_url 必须是 HTTPS URL，路径为 /wiki/<token>"
    space_name = destination.get("space_name")
    if not isinstance(space_name, str) or not space_name.strip():
        return "未配置 parent_wiki_url 时，destination.space_name 必须为非空字符串"
    node_path = destination.get("node_path")
    if node_path is not None:
        if not isinstance(node_path, list) or not node_path or any(
            not isinstance(part, str) or not part.strip() for part in node_path
        ):
            return "destination.node_path 必须为非空字符串数组或 null"
    else:
        title = destination.get("node_title")
        if not isinstance(title, str) or not title.strip():
            return "未配置 node_path 时，destination.node_title 必须为非空字符串"
    return None


def check(config_path=None, timeout=30):
    checks = []
    missing = []

    def record(name, passed, reason=None, **details):
        checks.append({"dependency": name, "passed": passed, **details})
        if not passed:
            missing.append({"dependency": name, "reason": reason or "检查失败"})

    selected = Path(config_path).expanduser() if config_path else SKILL_DIRECTORY / "config.local.json"
    if not config_path and not selected.exists():
        selected = SKILL_DIRECTORY / "config.example.json"
    selected = selected.resolve()
    config = {}
    try:
        config = json.loads(selected.read_text(encoding="utf-8-sig"))
        if not isinstance(config, dict):
            raise ValueError("配置必须是 JSON 对象")
    except (OSError, UnicodeError, ValueError):
        record("config", False, "配置文件缺失、不可读或不是 JSON 对象", path=str(selected))
        config = {}
    else:
        record("config", type(config.get("schema_version")) is int and config.get("schema_version") == 1,
               "schema_version 必须为 1", path=str(selected))

    routing_error = destination_error(config.get("destination"))
    record("config.destination", routing_error is None, routing_error)

    configured_roots = config.get("skill_roots", [])
    if not isinstance(configured_roots, list) or any(not isinstance(x, str) or not x.strip() for x in configured_roots):
        record("config.skill_roots", False, "skill_roots 必须是路径字符串数组")
        configured_roots = []
    roots = []
    for value in configured_roots:
        candidate = Path(value).expanduser()
        roots.append(candidate if candidate.is_absolute() else selected.parent / candidate)
    roots.extend([SKILL_DIRECTORY.parent, Path.cwd() / ".agents" / "skills", Path.home() / ".agents" / "skills"])
    codex_home = os.environ.get("CODEX_HOME")
    roots.append(Path(codex_home).expanduser() / "skills" if codex_home else Path.home() / ".codex" / "skills")
    roots = list(dict.fromkeys(path.resolve() for path in roots))
    for name, references in CORE_FILES.items():
        found = None
        for root in roots:
            for candidate in (root / name, root):
                skill = candidate / "SKILL.md"
                if readable_file(skill) and frontmatter_name(skill) == name:
                    found = candidate
                    break
            if found:
                break
        if found is None:
            record("skill:" + name, False, "未找到可读且 frontmatter name 匹配的 SKILL.md")
            continue
        absent = [ref for ref in references if not readable_file(found / ref)]
        record("skill:" + name, not absent,
               "缺少核心文件：" + ", ".join(absent), path=str(found), missing_core_files=absent)

    settings = config.get("tools", {})
    if not isinstance(settings, dict):
        record("config.tools", False, "tools 必须是 JSON 对象")
        settings = {}
    resolved = {}
    for name, args in COMMANDS.items():
        override = settings.get(name) if name == "hypit" else None
        launcher, reason = resolve_tool(name, override)
        if not launcher:
            record("tool:" + name, False, reason)
            continue
        resolved[name] = launcher
        passed, output, reason = run_local([launcher, *args], timeout)
        details = {"path": launcher}
        if passed and name == "node":
            match = re.search(r"\bv(\d+)\.(\d+)\.(\d+)\b", output)
            version = tuple(map(int, match.groups())) if match else None
            passed = version is not None and version >= (22, 15, 0)
            reason = "Node.js 必须为 22.15.0 或更高版本"
            if version:
                details["version"] = ".".join(map(str, version))
        record("tool:" + name, passed, reason, **details)

    python = resolved.get("python3")
    if python:
        passed, _, reason = run_local([python, "-c", "import requests; print('requests_import_ok')"], timeout)
        record("python_module:requests", passed, reason or "所选 python3 无法导入 requests")
    else:
        record("python_module:requests", False, "缺少 python3，无法验证 requests")

    skills_cli = shutil.which("skills")
    skills_args = [skills_cli, "--version"] if skills_cli else None
    if not skills_args and resolved.get("npx"):
        skills_args = [resolved["npx"], "--no-install", "skills", "--version"]
    if skills_args:
        passed, _, reason = run_local(skills_args, timeout)
        record("tool:skills", passed, reason or "未找到现成 skills CLI；离线检查不会安装它",
               invocation=skills_args, offline=True)
    else:
        record("tool:skills", False, "未找到 skills CLI，且没有 npx 用于检查现成缓存")

    redfox_present = bool(os.environ.get("REDFOX_API_KEY", "").strip())
    record("environment:REDFOX_API_KEY", redfox_present, "需要配置非空 REDFOX_API_KEY（不要将值写入报告）")

    transcription = config.get("transcription", {})
    if not isinstance(transcription, dict):
        record("config.transcription", False, "transcription 必须是 JSON 对象")
        transcription = {}
    mode = transcription.get("mode")
    language = transcription.get("language")
    threads = transcription.get("threads")
    record("transcription.language", isinstance(language, str) and bool(language.strip()),
           "必须明确 transcription.language，例如 zh")
    record("transcription.threads", isinstance(threads, int) and not isinstance(threads, bool) and threads > 0,
           "transcription.threads 必须是正整数")
    if mode == "whisper-local":
        launcher, reason = resolve_tool("whisper", settings.get("whisper"))
        if launcher:
            passed, output, reason = run_local([launcher, "--help"], timeout)
            absent_flags = [flag for flag in WHISPER_REQUIRED_FLAGS if not re.search(
                r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])", output
            )]
            if passed and absent_flags:
                passed, reason = False, "Whisper CLI 缺少必需参数：" + ", ".join(absent_flags)
            record("transcription.whisper_cli", passed, reason, path=launcher)
        else:
            record("transcription.whisper_cli", False, reason)
        model, reason = resolve_whisper_model(transcription)
        record("transcription.model_file", model is not None, reason,
               **({"path": str(model)} if model else {}))
    elif mode == "hypit-transcribe":
        profile = absolute_existing_file(transcription.get("runtime_profile"))
        endpoint = transcription.get("endpoint")
        record("transcription.runtime_profile", profile is not None,
               "hypit-transcribe 需要已存在、非空、可读的绝对 runtime_profile 文件路径",
               **({"path": str(profile)} if profile else {}))
        record("transcription.endpoint", isinstance(endpoint, str) and bool(endpoint.strip()),
               "hypit-transcribe 必须显式配置 endpoint；此检查不验证服务可用性")
    else:
        record("transcription.mode", False, "mode 必须为 whisper-local 或 hypit-transcribe")

    return {
        "ok": not missing,
        "status": "local_dependencies_passed" if not missing else "local_dependencies_blocked",
        "config_path": str(selected),
        "checks": checks,
        "missing_dependencies": missing,
        "not_checked": [
            "online_skill_latest_gate",
            "authentication_permissions_and_redfox_balance_gate",
            "transcription_model_and_service_readiness_gate",
            "required_subcommand_compatibility_gate",
        ],
        "scope": "仅检查本地依赖、命令帮助/版本、Whisper 必需参数与文件存在性；不代表全流程就绪。Hypit/lark 所需子命令参数兼容性仍须通过后续 required_subcommand_compatibility_gate。未安装、升级或下载任何依赖。",
        "next_action": (
            "请用户安装、修复或配置缺失依赖后重新检查；本脚本不会代为安装或升级。"
            if missing else
            "继续执行独立的技能最新版本门禁、身份/权限门禁、模型/服务就绪门禁与所需子命令兼容性门禁。"
        ),
    }


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("--config", help="配置 JSON；默认优先 config.local.json，否则 config.example.json")
    parser.add_argument("--timeout", type=float, default=30, help="每条本地检查命令的超时秒数（1–120）")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout 必须在 1 到 120 秒之间")
    result = check(args.config, args.timeout)
    emit(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
