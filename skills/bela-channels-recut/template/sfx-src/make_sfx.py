# 合成电子数字音效：翻滚滴答、落定锁定、逐字弹出、标签数据声
import sys, wave, numpy as np
SR = 48000
out = sys.argv[1]

def soft_square(f, t, k=3):
    # 奇次谐波叠加，比纯方波柔和
    return sum(np.sin(2 * np.pi * f * (2 * n + 1) * t) / (2 * n + 1) for n in range(k))

def env(t, attack, decay):
    return np.minimum(t / attack, 1) * np.exp(-t / decay)

def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.85
    with wave.open(f"{out}/{name}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

t = np.arange(int(SR * 0.03)) / SR
save("tick", soft_square(2600, t) * env(t, 0.0008, 0.006))

t1 = np.arange(int(SR * 0.06)) / SR
t2 = np.arange(int(SR * 0.11)) / SR
save("lock", np.concatenate([soft_square(1760, t1) * env(t1, 0.001, 0.03), soft_square(2640, t2) * env(t2, 0.001, 0.05)]))

t = np.arange(int(SR * 0.08)) / SR
f = 900 + 1100 * (t / t[-1])
save("blip", soft_square(1, np.cumsum(f) / SR) * env(t, 0.001, 0.025))

rng = np.random.default_rng(7)
parts = []
for i in range(9):
    tt = np.arange(int(SR * 0.022)) / SR
    parts.append(soft_square(rng.choice([1500, 1900, 2300, 2800, 3200]), tt) * env(tt, 0.0008, 0.007))
save("data", np.concatenate(parts))

# 可随模板分发的低音冲击和章节扫频。
t = np.arange(int(SR * 0.32)) / SR
bass_phase = 2 * np.pi * np.cumsum(55 + 95 * np.exp(-t / 0.035)) / SR
save("bass-hit-short", np.sin(bass_phase) * env(t, 0.004, 0.07))

t = np.arange(int(SR * 0.40)) / SR
sweep_phase = 2 * np.pi * np.cumsum(300 + 2400 * (t / t[-1]) ** 2) / SR
save("sweep-scifi-fast", np.sin(sweep_phase) * np.sin(np.pi * t / t[-1]) ** 2)
