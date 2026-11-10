#!/usr/bin/env bash
# 视频口播文案转写
# 输入: 视频文件路径 OR 直链 URL
# 输出: 转写文本到 stdout (也可指定 --out 落盘)
#
# 依赖: ffmpeg + whisper-cli + 模型文件
# 用法:
#   ./transcribe_video.sh /path/to/video.mp4
#   ./transcribe_video.sh "https://cdn.xhscdn.com/xxx.mp4"
#   ./transcribe_video.sh video.mp4 --out transcript.txt
#   ./transcribe_video.sh video.mp4 --lang zh|en|auto

set -euo pipefail

MODEL="${WHISPER_MODEL_PATH:-$HOME/.whisper-models/ggml-large-v3-turbo-q5_0.bin}"
LANG="zh"
OUT=""
INPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2;;
    --lang) LANG="$2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    -h|--help)
      sed -n '2,15p' "$0"; exit 0;;
    *) INPUT="$1"; shift;;
  esac
done

[[ -z "$INPUT" ]] && { echo "ERROR: 缺少输入 (视频路径或 URL)" >&2; exit 1; }

# 前置依赖检查
for bin in ffmpeg whisper-cli; do
  command -v "$bin" >/dev/null || { echo "ERROR: 缺少依赖 $bin。安装提示：brew install $bin" >&2; exit 2; }
done
[[ -f "$MODEL" ]] || {
  echo "ERROR: 找不到 whisper 模型: $MODEL" >&2
  echo "下载: curl -L -o $MODEL https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin" >&2
  exit 3
}

TMPDIR_X=$(mktemp -d)
trap 'rm -rf "$TMPDIR_X"' EXIT

# 输入是 URL 就先下载
if [[ "$INPUT" =~ ^https?:// ]]; then
  VID="$TMPDIR_X/in.mp4"
  curl -sL --max-time 60 -o "$VID" "$INPUT" || { echo "ERROR: 下载失败" >&2; exit 4; }
else
  VID="$INPUT"
  [[ -f "$VID" ]] || { echo "ERROR: 文件不存在: $VID" >&2; exit 5; }
fi

WAV="$TMPDIR_X/audio.wav"
ffmpeg -y -loglevel error -i "$VID" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV"

STEM="$TMPDIR_X/out"
whisper-cli -m "$MODEL" -l "$LANG" -f "$WAV" -otxt -of "$STEM" >&2

TXT="$STEM.txt"
[[ -f "$TXT" ]] || { echo "ERROR: 转写失败，无输出文件" >&2; exit 6; }

if [[ -n "$OUT" ]]; then
  cp "$TXT" "$OUT"
  echo "$OUT"
else
  cat "$TXT"
fi
