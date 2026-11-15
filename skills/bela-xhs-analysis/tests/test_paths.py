"""Tests for paths.py."""
import json
from pathlib import Path
from scripts.library.paths import (
    load_user_config,
    save_user_config,
    blogger_dir,
    notes_dir,
    images_dir,
    archive_dir,
    covers_dir,
    slides_dir,
    DEFAULT_CONFIG,
)


def test_load_user_config_returns_defaults_when_missing(tmp_path):
    config_path = tmp_path / "user-config.json"
    cfg = load_user_config(config_path)
    assert cfg["schema_version"] == "1.0"
    assert cfg["storage_root"] == "~/Documents/xhs-竞品分析"
    assert cfg["explosive_threshold_low"] == 1000


def test_save_user_config_writes_file(tmp_path):
    config_path = tmp_path / "user-config.json"
    custom = dict(DEFAULT_CONFIG)
    custom["storage_root"] = "/tmp/test-xhs"
    save_user_config(custom, config_path)
    assert config_path.exists()
    loaded = json.loads(config_path.read_text())
    assert loaded["storage_root"] == "/tmp/test-xhs"


def test_blogger_dir_composition(tmp_path):
    cfg = dict(DEFAULT_CONFIG)
    cfg["storage_root"] = str(tmp_path)
    p = blogger_dir(cfg, industry="AI工具", platform="xhs", name="姜饼探AI")
    assert p == tmp_path / "AI工具" / "小红书-姜饼探AI"


def test_blogger_dir_redid_disambiguation(tmp_path):
    cfg = dict(DEFAULT_CONFIG)
    cfg["storage_root"] = str(tmp_path)
    p = blogger_dir(cfg, industry="AI工具", platform="xhs",
                    name="姜饼探AI", redId="95475810861")
    assert p == tmp_path / "AI工具" / "小红书-姜饼探AI-95475810861"


def test_subpaths_under_blogger(tmp_path):
    cfg = dict(DEFAULT_CONFIG)
    cfg["storage_root"] = str(tmp_path)
    bdir = blogger_dir(cfg, industry="AI工具", platform="xhs", name="A")
    assert notes_dir(bdir) == bdir / "notes"
    assert archive_dir(bdir) == bdir / "notes" / "_archive"
    assert images_dir(bdir) == bdir / "images"
    assert covers_dir(bdir) == bdir / "images" / "covers"
    assert slides_dir(bdir, "slug1") == bdir / "images" / "slides" / "slug1"
