# -*- coding: utf-8 -*-
"""
TinyPNG API key 管理 + 配置概览
- 配置文件：~/.tiny-png-api.json
- 文件权限：0o600（仅当前用户可读写）
"""

import json
import os
import sys
from pathlib import Path

API_CONFIG_PATH = Path.home() / ".tiny-png-api.json"


def load_api_key():
    """从配置文件读取 API key，找不到返回 None。"""
    if not API_CONFIG_PATH.exists():
        return None
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        key = config.get("api_key", "").strip()
        return key or None
    except (json.JSONDecodeError, OSError):
        return None


def save_api_key(api_key):
    """保存 API key 到 ~/.tiny-png-api.json，权限 0o600。"""
    api_key = api_key.strip()
    if not api_key:
        print("❌ API key 不能为空")
        sys.exit(1)

    config = {"api_key": api_key}
    with open(API_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    try:
        os.chmod(API_CONFIG_PATH, 0o600)
    except OSError:
        pass


def unset_api_key():
    """删除已保存的 API key。返回是否真的删除了。"""
    if API_CONFIG_PATH.exists():
        try:
            API_CONFIG_PATH.unlink()
            return True
        except OSError:
            return False
    return False


def mask_key(key):
    """脱敏显示 API key（开头 4 位 + 中间星号 + 末尾 4 位）。"""
    if len(key) <= 8:
        return "****"
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def show_config():
    """打印当前配置概览（API key + 缓存状态 + HEIC 支持）。"""
    # 延迟导入，避免顶层循环依赖
    from cache import CACHE_PATH, load_cache, stats
    from utils import format_size
    from heic import ensure_support

    print("📊 bela-tiny-png 配置概览")
    print("─" * 56)

    # API key
    key = load_api_key()
    if key:
        print(f"🔑 API key      ✅ {mask_key(key)}")
        print(f"   配置文件     {API_CONFIG_PATH}")
    else:
        print("🔑 API key      ⚠️  未配置")
        print(f"   预期位置     {API_CONFIG_PATH}")

    # 缓存
    cache = load_cache()
    cache_stats = stats(cache)
    print()
    if cache_stats["count"] > 0:
        print(f"💾 处理缓存      {cache_stats['count']} 条记录"
              f"（累计节省 {format_size(cache_stats['saved_bytes'])}）")
    else:
        print("💾 处理缓存      （空）")
    print(f"   缓存文件     {CACHE_PATH}")

    # HEIC 支持
    print()
    if ensure_support():
        print("📷 HEIC/HEIF    ✅ 可用（pillow-heif 已安装）")
    else:
        print("📷 HEIC/HEIF    ⚠️  未启用")
        print("   开启方法     pip install pillow pillow-heif --break-system-packages")
