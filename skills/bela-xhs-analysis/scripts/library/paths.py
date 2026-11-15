"""Path resolution for S1.

负责 user-config.json 的读写 + 博主目录路径组装.
设计宪法 C5: 数据兜底流程 - 先读本地，没有就用默认.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

_SKILL_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _SKILL_ROOT / "user-config.json"

DEFAULT_CONFIG = {
    "schema_version": "1.0",
    "storage_root": "~/Documents/xhs-竞品分析",
    "persona_root": "~/Documents/个人档案",
    "default_industry": None,
    "explosive_threshold_low": 1000,
    "explosive_threshold_high": 5000,
    "fans_threshold": 2000,
    "archive_after_days": 180,
    "scan_depth_default": "standard",
    "ask_on_each_scan": True,
}

PLATFORM_DISPLAY = {
    "xhs": "小红书",
}


def load_user_config(path: Optional[Path] = None) -> dict:
    """加载用户配置；不存在则返回默认副本."""
    path = path or _DEFAULT_CONFIG_PATH
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    return json.loads(path.read_text(encoding="utf-8"))


def save_user_config(cfg: dict, path: Optional[Path] = None) -> None:
    """保存用户配置."""
    path = path or _DEFAULT_CONFIG_PATH
    path.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def storage_root(cfg: dict) -> Path:
    """从 cfg 拿 storage_root 并展开 ~."""
    return Path(cfg["storage_root"]).expanduser()


def blogger_dir(
    cfg: dict,
    *,
    industry: str,
    platform: str,
    name: str,
    redId: Optional[str] = None,
) -> Path:
    """组装博主目录路径.

    规则：{storage_root}/{industry}/{平台显示名}-{name}[-{redId}]
    """
    platform_zh = PLATFORM_DISPLAY.get(platform, platform)
    folder = f"{platform_zh}-{name}"
    if redId:
        folder = f"{folder}-{redId}"
    return storage_root(cfg) / industry / folder


def notes_dir(bdir: Path) -> Path:
    return bdir / "notes"


def archive_dir(bdir: Path) -> Path:
    return bdir / "notes" / "_archive"


def images_dir(bdir: Path) -> Path:
    return bdir / "images"


def covers_dir(bdir: Path) -> Path:
    return bdir / "images" / "covers"


def slides_dir(bdir: Path, slug: str) -> Path:
    return bdir / "images" / "slides" / slug


def meta_path(bdir: Path) -> Path:
    return bdir / "_meta.json"


def readme_path(bdir: Path) -> Path:
    return bdir / "README.md"
