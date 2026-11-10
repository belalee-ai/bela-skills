#!/usr/bin/env bash
# Regression test — runs every time you change the skill, to catch breakage.
#
# Fixtures: put your own sample files in `tests/fixtures/` (gitignored).
#   - images/*.png       (image-text note pages, for OCR)
#   - videos/*.mp4       (video notes, for transcription)
# If no fixtures are present, only the in-memory unit test (Top-5 comment sorting)
# is run. That's enough to confirm the install is healthy.
#
# Usage:
#   ./run_regression.sh

set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURES="$SKILL_DIR/tests/fixtures"
OUT_DIR="${XHS_REGRESSION_DIR:-/tmp/xhs_regression}"
mkdir -p "$OUT_DIR"

PASS=0
FAIL=0
SKIP=0

check() {
  local name="$1" expected_substr="$2" actual_file="$3"
  if [[ ! -f "$actual_file" ]]; then
    echo "  ❌ FAIL: $name → output file missing: $actual_file"; ((FAIL++)); return
  fi
  if grep -qF "$expected_substr" "$actual_file"; then
    echo "  ✅ PASS: $name"; ((PASS++))
  else
    echo "  ❌ FAIL: $name → expected '$expected_substr' not found in $actual_file"; ((FAIL++))
  fi
}

echo "=========================================="
echo "  bela-xhs-analysis regression"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# --- Dependency check ---
echo ""
echo "📋 Dependencies"
for bin in ffmpeg whisper-cli swift python3; do
  if command -v "$bin" >/dev/null; then echo "  ✅ $bin"; ((PASS++)); else echo "  ❌ $bin missing"; ((FAIL++)); fi
done
MODEL="${WHISPER_MODEL_PATH:-$HOME/.whisper-models/ggml-large-v3-turbo-q5_0.bin}"
if [[ -f "$MODEL" ]]; then echo "  ✅ whisper model: $MODEL"; ((PASS++)); else echo "  ❌ whisper model missing: $MODEL (run install.sh)"; ((FAIL++)); fi

# --- Case 1: Image OCR (fixtures optional) ---
echo ""
echo "📋 Image OCR"
if [[ -d "$FIXTURES/images" ]] && [[ $(ls "$FIXTURES/images"/*.png 2>/dev/null | wc -l) -gt 0 ]]; then
  n=$(ls "$FIXTURES/images"/*.png | wc -l | tr -d ' ')
  echo "  ℹ️  found $n image fixture(s) in $FIXTURES/images/"
  ls "$FIXTURES/images"/*.png | "$SKILL_DIR/scripts/media/ocr_images.sh" --out "$OUT_DIR/case_ocr.txt" >/dev/null 2>&1
  if [[ -s "$OUT_DIR/case_ocr.txt" ]]; then
    echo "  ✅ PASS: OCR ran without error, output non-empty"; ((PASS++))
  else
    echo "  ❌ FAIL: OCR produced empty output"; ((FAIL++))
  fi
else
  echo "  ⏭  SKIP: no images in $FIXTURES/images/ — add some .png files to enable this test"
  ((SKIP++))
fi

# --- Case 2: Video transcription (fixtures optional) ---
echo ""
echo "📋 Video transcription"
if [[ -d "$FIXTURES/videos" ]] && [[ $(ls "$FIXTURES/videos"/*.{mp4,wav,m4a} 2>/dev/null | wc -l) -gt 0 ]]; then
  for vid in "$FIXTURES/videos"/*.{mp4,wav,m4a}; do
    [[ -f "$vid" ]] || continue
    name=$(basename "$vid")
    "$SKILL_DIR/scripts/media/transcribe_video.sh" "$vid" --out "$OUT_DIR/case_video_$name.txt" >/dev/null 2>&1
    if [[ -s "$OUT_DIR/case_video_$name.txt" ]]; then
      lines=$(wc -l < "$OUT_DIR/case_video_$name.txt" | tr -d ' ')
      echo "  ✅ PASS: $name → $lines lines transcribed"; ((PASS++))
    else
      echo "  ❌ FAIL: $name → empty transcript"; ((FAIL++))
    fi
  done
else
  echo "  ⏭  SKIP: no videos in $FIXTURES/videos/ — add some .mp4/.wav files to enable this test"
  ((SKIP++))
fi

# --- Case 3: In-memory unit test (no fixtures needed) ---
echo ""
echo "📋 Top-5 comment sorting + unit parsing (offline, no fixtures)"
python3 -c "
import sys; sys.path.insert(0, '$SKILL_DIR/scripts')
import xhs_scraper as x
out = x.generate_note_markdown([{
    'note_id': 't', 'title': 'T', 'desc': 'd',
    'likes': '0', 'collects': '0', 'comments': '5', 'shares': '0', 'tags': [],
    'comment_list': [
        {'content':'C200','likes':200,'nickname':'u1'},
        {'content':'wan','likes':'1万+','nickname':'u2'},
        {'content':'big','likes':'2.5w','nickname':'u3'},
        {'content':'pipe | inside','likes':50,'nickname':'u4'},
    ],
    'author': {'nickname':'A','userId':'x'}, 'type': 'normal',
}])
print(out)
" > "$OUT_DIR/case_top5.md" 2>&1
first_row=$(awk '/Top [0-9]+ /{flag=1; next} flag && /^\| 1 /{print; exit}' "$OUT_DIR/case_top5.md")
if echo "$first_row" | grep -q "big"; then
  echo "  ✅ PASS: 2.5w ranked #1"; ((PASS++))
else
  echo "  ❌ FAIL: ranking wrong, got: $first_row"; ((FAIL++))
fi
if grep -q '\\|' "$OUT_DIR/case_top5.md"; then
  echo "  ✅ PASS: pipe-char escaped in table"; ((PASS++))
else
  echo "  ❌ FAIL: pipe not escaped"; ((FAIL++))
fi

# --- Summary ---
echo ""
echo "=========================================="
echo "  Result: ✅ $PASS passed / ❌ $FAIL failed / ⏭ $SKIP skipped"
echo "  Logs: $OUT_DIR/"
echo "=========================================="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
