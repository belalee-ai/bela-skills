#!/usr/bin/env bash
# 批量图片 OCR (中文优化)
# 输入: 图片 URL 列表 (stdin) OR 本地图片路径 (参数)
# 输出: 每张图的 OCR 结果，按 === <index> === 分隔
#
# 依赖: ffmpeg (webp→png) + swift (macOS Vision)
# 用法:
#   echo -e "url1\nurl2\nurl3" | ./ocr_images.sh
#   ./ocr_images.sh img1.png img2.png
#   ./ocr_images.sh --urls-file urls.txt
#   ./ocr_images.sh --out result.txt   # 落盘
#
# 平台: 仅 macOS (依赖 Vision Framework)。非 macOS 请用 PaddleOCR / Tesseract 替代实现。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OCR_SWIFT="$SCRIPT_DIR/ocr_image.swift"
OUT=""
URLS_FILE=""
INPUTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2;;
    --urls-file) URLS_FILE="$2"; shift 2;;
    -h|--help) sed -n '2,16p' "$0"; exit 0;;
    *) INPUTS+=("$1"); shift;;
  esac
done

# 平台检查
[[ "$(uname)" == "Darwin" ]] || { echo "ERROR: 此脚本仅支持 macOS (Vision Framework)" >&2; exit 10; }
command -v swift >/dev/null || { echo "ERROR: 未安装 Xcode Command Line Tools (swift)" >&2; exit 11; }
[[ -f "$OCR_SWIFT" ]] || { echo "ERROR: 未找到 $OCR_SWIFT" >&2; exit 12; }

TMPDIR_X=$(mktemp -d)
trap 'rm -rf "$TMPDIR_X"' EXIT

# 收集输入: stdin / --urls-file / 参数。每条按内容分流 → URL 或本地路径
URLS=()
LOCAL=()
classify() {
  local x="$1"
  [[ -z "$x" ]] && return
  if [[ "$x" =~ ^https?:// ]]; then URLS+=("$x"); else LOCAL+=("$x"); fi
}
if [[ -n "$URLS_FILE" ]]; then
  while IFS= read -r line; do classify "$line"; done < "$URLS_FILE"
fi
if [[ ! -t 0 ]] && [[ ${#INPUTS[@]} -eq 0 ]] && [[ -z "$URLS_FILE" ]]; then
  while IFS= read -r line; do classify "$line"; done
fi
if [[ ${#INPUTS[@]} -gt 0 ]]; then for x in "${INPUTS[@]}"; do classify "$x"; done; fi

# 下载 URL → 本地 PNG
i=0
[[ ${#URLS[@]} -eq 0 ]] && URLS=()
for url in ${URLS[@]+"${URLS[@]}"}; do
  ext="webp"
  [[ "$url" =~ \.jpg|\.jpeg ]] && ext="jpg"
  [[ "$url" =~ \.png ]] && ext="png"
  fname=$(printf "%03d.%s" "$i" "$ext")
  curl -sL --max-time 30 -o "$TMPDIR_X/$fname" "$url" || { echo "WARN: 下载失败 $url" >&2; ((i++)); continue; }
  if [[ "$ext" == "webp" ]]; then
    ffmpeg -y -loglevel error -i "$TMPDIR_X/$fname" "$TMPDIR_X/$(printf '%03d.png' "$i")" 2>/dev/null || true
    rm -f "$TMPDIR_X/$fname"
  elif [[ "$ext" != "png" ]]; then
    ffmpeg -y -loglevel error -i "$TMPDIR_X/$fname" "$TMPDIR_X/$(printf '%03d.png' "$i")" 2>/dev/null || true
    rm -f "$TMPDIR_X/$fname"
  fi
  ((i++))
done

# 拼接最终 OCR 输入
FILES=()
for f in $(ls "$TMPDIR_X"/*.png 2>/dev/null | sort); do FILES+=("$f"); done
if [[ ${#LOCAL[@]} -gt 0 ]]; then for f in "${LOCAL[@]}"; do [[ -f "$f" ]] && FILES+=("$f"); done; fi
[[ ${#FILES[@]} -eq 0 ]] && { echo "ERROR: 没有可处理的图片" >&2; exit 13; }

# 调用 OCR
if [[ -n "$OUT" ]]; then
  swift "$OCR_SWIFT" "${FILES[@]}" > "$OUT"
  echo "$OUT"
else
  swift "$OCR_SWIFT" "${FILES[@]}"
fi
