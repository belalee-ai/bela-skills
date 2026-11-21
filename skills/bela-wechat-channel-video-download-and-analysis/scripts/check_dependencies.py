#!/usr/bin/env python3
"""Inspect the local tools for downloading and analysing one WeChat Channels video."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import user_config


SKILL_DIRECTORY = Path(__file__).resolve().parent.parent
CORE_FILES = {
    "qiaomu-download": ("scripts/download.py", "references/wechat-video.md"),
    "wechat-video-downloader": ("scripts/parse_video_download.py",),
    "hypit": ("references/creation/reference-video.md",),
}
COMMANDS = {
    "hypit": ["media", "--help"], "ffmpeg": ["-version"], "ffprobe": ["-version"],
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
    env = {key: os.environ[key] for key in os.environ if key != "REDFOX_API_KEY"}
    env.update({
        "npm_config_offline": "true", "NPM_CONFIG_OFFLINE": "true",
        "npm_config_yes": "false", "npm_config_update_notifier": "false",
        "NO_UPDATE_NOTIFIER": "1", "CI": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
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


def resolve_tool(name, override=None, workspace_dirs=()):
    if override is not None:
        if not isinstance(override, str):
            return None, "配置必须是绝对启动器路径或 null"
        path = Path(override).expanduser()
        if not path.is_absolute():
            return None, "配置的启动器必须使用绝对路径"
        if not readable_file(path) or not os.access(path, os.X_OK):
            return None, "配置的启动器不存在、为空、不可读或不可执行"
        return str(path), None
    if name == "hypit":
        for directory in workspace_dirs:
            project_cli = directory / "node_modules" / ".bin" / ("hypit.cmd" if os.name == "nt" else "hypit")
            if project_cli.is_file() and os.access(project_cli, os.X_OK):
                return str(project_cli), None
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
    filename = {"large": "large-v3", "turbo": "large-v3-turbo"}.get(name, name)
    candidate = whisper_cache_directory() / (filename + ".pt")
    if readable_file(candidate):
        return candidate, None
    return None, "Whisper 缓存中没有已下载的模型文件：" + str(candidate)


def project_directories(workspace):
    if workspace:
        return [Path(workspace).expanduser().resolve()]
    cwd = Path.cwd()
    directories = []
    for directory in (cwd, *cwd.parents):
        directories.append(directory)
        if (directory / ".git").exists():
            return directories
    return [cwd]


def standard_skill_roots(workspace_dirs):
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME") or home / ".codex").expanduser()
    claude_home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude").expanduser()
    grok_home = Path(os.environ.get("GROK_HOME") or home / ".grok").expanduser()
    roots = [directory / agent / "skills" for directory in workspace_dirs
             for agent in (".agents", ".claude", ".gemini", ".grok")]
    # A symlinked Skill can have siblings in its installation or its source checkout.
    install_parent = Path(__file__).absolute().parent.parent.parent
    return [
        *roots, install_parent, SKILL_DIRECTORY.parent, home / ".agents/skills",
        codex_home / "skills", claude_home / "skills", home / ".gemini/skills", grok_home / "skills",
    ]


def check_transcription(config, settings, timeout, record):
    transcription = config.get("transcription", {})
    if not isinstance(transcription, dict):
        record("config.transcription", False, "transcription 必须是 JSON 对象")
        transcription = {}
    mode = transcription.get("mode")
    language = transcription.get("language")
    threads = transcription.get("threads")
    record("transcription.language", isinstance(language, str) and bool(language.strip()),
           "必须明确 transcription.language，例如 zh")
    if mode == "whisper-local":
        record("transcription.threads", type(threads) is int and threads > 0,
               "transcription.threads 必须是正整数")
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


def check(config_path=None, timeout=30, download_only=False, download_provider=None,
          workspace=None, skill_roots=()):
    checks = []
    missing = []

    def record(name, passed, reason=None, **details):
        checks.append({"dependency": name, "passed": passed, **details})
        if not passed:
            missing.append({"dependency": name, "reason": reason or "检查失败"})

    selected = Path(config_path).expanduser().resolve() if config_path else user_config.config_path()
    try:
        if config_path:
            config = user_config.read_json(selected)
            if config["schema_version"] == 2:
                user_config.clean_delivery(config.get("delivery"))
        else:
            config = user_config.read_preferences()
        saved_provider = user_config.clean_download(config.get("download", {}))["provider"]
        provider = saved_provider if download_provider is None else download_provider
        if provider is not None and provider not in user_config.DOWNLOAD_PROVIDERS:
            raise ValueError("未知下载器，可选择红狐 wechat-video-downloader 或乔木 qiaomu-download")
    except (OSError, ValueError) as error:
        record("config", False, str(error), path=str(selected))
        return {
            "ok": False, "status": "local_dependencies_blocked", "config_path": str(selected),
            "checks": checks, "missing_dependencies": missing, "next_action": "请修复原配置后重新检查。",
        }
    record("config", True, path=str(selected))
    if provider is None:
        return {
            "ok": False, "status": "download_provider_required", "config_path": str(selected),
            "download_provider": None, "available_providers": list(user_config.DOWNLOAD_PROVIDERS),
            "checks": checks, "missing_dependencies": [],
            "next_action": "推荐红狐（需 API Key），也可选乔木。请用户选择并保存偏好，若明确仅本次则用 --download-provider。",
        }

    configured_roots = config.get("skill_roots", [])
    if not isinstance(configured_roots, list) or any(not isinstance(x, str) or not x.strip() for x in configured_roots):
        record("config.skill_roots", False, "skill_roots 必须是路径字符串数组")
        configured_roots = []
    roots = [Path(value).expanduser() for value in skill_roots]
    for value in configured_roots:
        candidate = Path(value).expanduser()
        roots.append(candidate if candidate.is_absolute() else selected.parent / candidate)
    workspace_dirs = project_directories(workspace)
    roots.extend(standard_skill_roots(workspace_dirs))
    roots = list(dict.fromkeys(path.resolve() for path in roots))
    required_skills = [provider] if download_only else [provider, "hypit"]
    for name in required_skills:
        references = CORE_FILES[name]
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
    minimum = (3, 10) if provider == "qiaomu-download" else (3, 8)
    record("tool:python3", sys.version_info >= minimum,
           f"{provider} 需要 Python {minimum[0]}.{minimum[1]} 或更高版本", path=sys.executable)
    required_tools = ["ffmpeg", "ffprobe"] if download_only else ["ffmpeg", "ffprobe", "hypit"]
    for name in required_tools:
        override = settings.get(name) if name == "hypit" else None
        launcher, reason = resolve_tool(name, override, workspace_dirs)
        if not launcher:
            record("tool:" + name, False, reason)
            continue
        passed, _, reason = run_local([launcher, *COMMANDS[name]], timeout)
        record("tool:" + name, passed, reason, path=launcher)
        if name == "hypit":
            record("hypit.media", passed, reason)

    if provider == "wechat-video-downloader":
        passed, _, _ = run_local(
            [sys.executable, "-c", "import requests; print(requests.__version__)"], timeout
        )
        record("python:requests", passed, "tool:python3 对应的环境未能导入 requests，请在该环境中安装或修复此包",
               path=sys.executable)

    if not download_only:
        check_transcription(config, settings, timeout, record)

    return {
        "ok": not missing,
        "status": "local_dependencies_passed" if not missing else "local_dependencies_blocked",
        "download_provider": provider,
        "config_path": str(selected),
        "checks": checks,
        "missing_dependencies": missing,
        "not_checked": ["wechat_media_access", "remote_skill_updates", "transcription_inference"],
        "next_action": (
            "按 references/setup-and-updates.md 安装缺少的普通依赖并复检；配置错误按原选择修正。"
            if missing else "使用已定位的下载器和工具处理本次链接。"
        ),
    }


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("--config", help="只读使用指定 v1/v2 JSON；默认使用用户主目录中的个人配置")
    parser.add_argument("--timeout", type=float, default=30, help="每条本地检查命令的超时秒数（1–120）")
    parser.add_argument("--download-only", action="store_true", help="只检查视频下载与文件验证所需的依赖")
    parser.add_argument("--download-provider", choices=user_config.DOWNLOAD_PROVIDERS,
                        help="仅本次使用指定下载器。推荐红狐 wechat-video-downloader，也可选乔木 qiaomu-download")
    parser.add_argument("--workspace", type=Path, help="从临时目录执行时，指定实际项目根目录以查找已安装依赖")
    parser.add_argument("--skill-root", type=Path, action="append", default=[],
                        help="优先搜索 Agent 提供的 Skill 目录或其父目录，可重复指定，仅本次生效")
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout 必须在 1 到 120 秒之间")
    if args.workspace is not None and not args.workspace.expanduser().is_dir():
        parser.error("--workspace 必须指向现有项目目录")
    result = check(args.config, args.timeout, args.download_only, args.download_provider,
                   args.workspace, args.skill_root)
    emit(result)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
