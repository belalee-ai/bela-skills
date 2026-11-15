# 口播粗剪：按保留区间拼接原片，整体变速一次（atempo 保留音高）
# 用法：python3 rough_cut.py 原视频.MOV 粗剪.mp4 1.2 keep.json
# keep.json 是原片秒数的保留区间列表，如 [[0.74, 17.62], [19.50, 42.14]]
import json, subprocess, sys

SRC, OUT, SPEED, KEEP = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
keep = json.load(open(KEEP))
f = []; vs = []
for i, (s, e) in enumerate(keep):
    d = e - s
    f.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
    f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={d-0.015:.3f}:d=0.015[a{i}]")
    vs.append(f"[v{i}][a{i}]")
f.append("".join(vs) + f"concat=n={len(keep)}:v=1:a=1[vc][ac]")
f.append(f"[vc]setpts=PTS/{SPEED},fps=30[vo]")
f.append(f"[ac]atempo={SPEED},aresample=48000[ao]")
cmd = ["ffmpeg", "-y", "-v", "error", "-i", SRC, "-filter_complex", ";".join(f), "-map", "[vo]", "-map", "[ao]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
       "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
kept = sum(e - s for s, e in keep)
print("src kept:", round(kept, 2), "s ->", round(kept / SPEED, 2), "s")
