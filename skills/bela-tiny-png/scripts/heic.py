# -*- coding: utf-8 -*-
"""
HEIC / HEIF 支持 —— iPhone 默认拍摄格式

TinyPNG 原生不支持 HEIC，需要先用 Pillow + pillow-heif 转成 JPEG。
依赖：pip install pillow pillow-heif --break-system-packages

未安装时，HEIC 文件会被自动跳过（但其它格式不受影响）。
"""

import tempfile
from pathlib import Path

HEIC_EXTENSIONS = {".heic", ".heif"}
_loaded = False
_load_failed = False


def is_heic(path):
    return Path(path).suffix.lower() in HEIC_EXTENSIONS


def ensure_support():
    """尝试加载 pillow-heif；返回 True 表示可用。失败会缓存以免重复打印。"""
    global _loaded, _load_failed
    if _loaded:
        return True
    if _load_failed:
        return False
    try:
        from PIL import Image  # noqa: F401
        import pillow_heif
        pillow_heif.register_heif_opener()
        _loaded = True
        return True
    except ImportError:
        _load_failed = True
        return False


def install_hint():
    return ("⚠️  发现 HEIC/HEIF 文件，但缺少依赖。请运行：\n"
            "     pip install pillow pillow-heif --break-system-packages\n"
            "   未安装时 HEIC 文件会被跳过。")


def heic_to_temp_jpeg(heic_path, quality=95):
    """把 HEIC 转成临时 JPEG，返回临时文件路径。调用方负责删除。"""
    from PIL import Image
    img = Image.open(str(heic_path))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, prefix="bela_tinypng_")
    tmp.close()
    img.save(tmp.name, "JPEG", quality=quality)
    return Path(tmp.name)
