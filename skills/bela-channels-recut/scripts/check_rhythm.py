# 节奏检查：列出 data.ts 里超过 N 秒（默认 3）没有任何变化点的区间
# 变化点 = 镜头切换、花字、标签、章节、冲击、额外音效、推近等所有 from/at
# 用法：python3 check_rhythm.py src/data.ts [3.0]
import re, sys
s = open(sys.argv[1]).read()
limit = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
s = s[:s.index("export const CUES")] if "export const CUES" in s else s
ev = {float(x) for x in re.findall(r"\b(?:from|at|tagAt|peakAt|footAt|shrinkAt|growAt): ([\d.]+)", s)}
ev |= {float(x) for x in re.findall(r"\b(?:slow|fast): \[([\d.]+)", s)}  # 自制段落内部的动画起点
for name in ("IMPACTS", "PUNCH_INS"):
    m = re.search(name + r" = \[([^\]]*)\]", s)
    if m: ev |= {float(x) for x in m.group(1).split(",") if x.strip()}
total = float(re.search(r"TOTAL_SECONDS = ([\d.]+)", s).group(1))
ev = sorted(ev | {0.0, total})
gaps = [(a, b, round(b - a, 2)) for a, b in zip(ev, ev[1:]) if b - a > limit]
print(f"{len(ev)} 个变化点，最长间隔 {max(b - a for a, b in zip(ev, ev[1:])):.2f} 秒")
for a, b, d in gaps: print(f"  超过 {limit} 秒：{a}–{b}（{d} 秒）")
sys.exit(1 if gaps else 0)
