#!/bin/zsh
# 整片分段渲染：每 900 帧一段（各自新开浏览器，避免长段内存崩溃），画面无损拼接，声音整条单独渲染后合成
# 用法：./render.sh ../精剪初版.mp4
set -e
OUT=${1:-../精剪初版.mp4}
TMP=$(mktemp -d)
TOTAL=$(python3 -c "import re;s=open('src/data.ts').read();print(round(float(re.search(r'TOTAL_SECONDS = ([\d.]+)',s).group(1))*30))")
OPTS=(--timeout=120000 --concurrency=2 --offthreadvideo-cache-size-in-bytes=536870912 --log=error)
python3 make_font_subset.py
i=0; : > $TMP/list.txt
for ((s=0; s<TOTAL; s+=900)); do
  e=$((s+899)); (( e > TOTAL-1 )) && e=$((TOTAL-1))
  npx remotion render src/index.ts Main $TMP/part$i.mp4 --frames=$s-$e --codec=h264 --crf=18 --muted "${OPTS[@]}"
  echo "file '$TMP/part$i.mp4'" >> $TMP/list.txt
  i=$((i+1))
done
npx remotion render src/index.ts Main $TMP/audio.aac --codec=aac "${OPTS[@]}"
ffmpeg -v error -y -f concat -safe 0 -i $TMP/list.txt -i $TMP/audio.aac -map 0:v -map 1:a -c copy -movflags +faststart "$OUT"
echo "done: $OUT"
