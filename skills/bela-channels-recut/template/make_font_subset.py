# 改了标题、花字、标签或字幕文字后重跑：把思源黑体裁成只含本片用到的字，渲染时字体秒加载
import subprocess
txt = open("src/data.ts").read() + open("src/Main.tsx").read()
chars = {c for c in txt if ord(c) > 127} | {chr(i) for i in range(32, 127)}
u = ",".join(f"U+{ord(c):04X}" for c in sorted(chars))
subprocess.run(["pyftsubset", "public/fonts/NotoSansSC.ttf", f"--unicodes={u}",
                "--output-file=public/fonts/NotoSansSC-sub.ttf", "--layout-features=*"], check=True)
