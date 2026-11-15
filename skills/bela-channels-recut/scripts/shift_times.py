# 粗剪剪掉一段后，平移 data.ts 里切点之后的所有成片时间
# 用法：python3 shift_times.py src/data.ts <切点成片秒> <减少秒数>
# 减少秒数 = 删掉的原片秒数 / 倍速。落在被删区间里的值钉到切点；素材入点 start 不动
import re, sys
p, cut, d = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
s = open(p).read()
fmt = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
def sh(v):
    v = float(v)
    return None if v <= cut else fmt(max(cut, round(v - d, 2)))
n = 0
def rep(m):
    global n
    nv = sh(m.group(2))
    if nv is None: return m.group(0)
    n += 1; return f"{m.group(1)}: {nv}"
s = re.sub(r"\b(from|to|at|tagAt|peakAt|footAt|growAt): ([\d.]+)", rep, s)
for name in ("IMPACTS", "PUNCH_INS"):
    m = re.search(name + r" = \[([^\]]*)\]", s)
    if m: s = s.replace(m.group(0), f"{name} = [{', '.join(sh(x.strip()) or x.strip() for x in m.group(1).split(','))}]")
s = re.sub(r"TOTAL_SECONDS = ([\d.]+)", lambda m: f"TOTAL_SECONDS = {fmt(float(m.group(1)) - d)}", s)
open(p, "w").write(s)
print(f"平移了 {n} 个时间值；TOTAL_SECONDS 减 {d}")
