import React from "react";
import {
  AbsoluteFill, Audio, Sequence, cancelRender, getInputProps, continueRender, delayRender, Easing,
  interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { Video } from "@remotion/media";
import { CHAPTERS, CUES, EXTRA_SFX, FLOWERS, IMPACTS, LABELS, MOUNTAIN_TAGS, PIP, SPEED, PUNCH_INS, SHOTS, TITLE, TWO_LINES } from "./data";

const LIME = "#9CF93D";
const CYAN = "#4FE3F0";
// 音效整体增益：用户 2026-11-03 说音效偏高，降 10%；以后整体调大小只改这里
const SFX_GAIN = 0.9;
// 版式方案切换（渲染时用 --props 传入）：bg 背景 / title 标题第二行配色 / mark 账号名位置
const LOOK = { bg: "diag", title: "lime", mark: "none", ...(getInputProps() as Record<string, string>) };
const BAND = { top: 420, h: 596 };
const CIRCLE = { cx: 540, top: 1270, d: 400 };
// 原片里取圆镜的焦点与取景宽度：头顶完整露出并留少量空白，下到胸口；避开左上红三角
const FOCUS = { x: 540, y: 690, side: 1080 };

// 每个字体单独加载：8 秒没回来就重试，最多 3 次；失败会在渲染日志里报出字体名
// 等字体的 delayRender 放在 Main 组件里，只在真正渲染画面的页面生效
const loadFont = async (family: string, file: string, desc: FontFaceDescriptors = {}) => {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const face = new FontFace(family, `url(${staticFile(file)}?v=${attempt})`, desc);
      await Promise.race([face.load(), new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), 8000))]);
      document.fonts.add(face);
      return;
    } catch (e) {
      console.error(`[font] ${family} attempt ${attempt} failed: ${e}`);
    }
  }
  throw new Error(`[font] ${family} could not load`);
};
const fontsReady = Promise.all([
  loadFont("Smiley", "fonts/SmileySans-Oblique.ttf"),
  loadFont("NotoSC", "fonts/NotoSansSC-sub.ttf", { weight: "100 900" }),
  loadFont("Orbitron", "fonts/Orbitron.ttf", { weight: "400 900" }),
]);

const ease = Easing.bezier(0.65, 0, 0.35, 1);

// 0 = 大人像，1 = 小圆镜
const pipProgress = (t: number) => {
  const a = interpolate(t, [PIP.shrinkAt, PIP.shrinkAt + PIP.dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const b = interpolate(t, [PIP.growAt, PIP.growAt + PIP.dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  return t < PIP.growAt ? a : b;
};

const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

const ARoll: React.FC<{ t: number }> = ({ t }) => {
  const p = pipProgress(t);
  const w = lerp(1080, CIRCLE.d, p);
  const h = lerp(1920, CIRCLE.d, p);
  const x = lerp(0, CIRCLE.cx - CIRCLE.d / 2, p);
  const y = lerp(0, CIRCLE.top, p);
  const scale = lerp(1, CIRCLE.d / FOCUS.side, p);
  const fx = 540;
  const fy = lerp(960, FOCUS.y, p);
  // 结尾大人像推近：每过一个节点在 1.0 / 1.1 之间切换，0.15 秒到位
  const passed = PUNCH_INS.filter((a) => t >= a);
  const last = passed.length ? passed[passed.length - 1] : -10;
  const target = passed.length % 2 === 1 ? 1.1 : 1;
  const prev = passed.length % 2 === 1 ? 1 : 1.1;
  const punch = passed.length ? interpolate(t, [last, last + 0.15], [prev, target], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) : 1;
  return (
    <div style={{
      position: "absolute", left: x, top: y, width: w, height: h, overflow: "hidden",
      borderRadius: lerp(0, CIRCLE.d / 2, p),
      boxShadow: p > 0.01 ? `0 0 0 ${5 * p}px rgba(255,255,255,0.92), 0 18px 50px rgba(0,0,0,0.55)` : undefined,
    }}>
      <div style={{ position: "absolute", inset: 0, transform: `scale(${punch})`, transformOrigin: "50% 36%" }}>
        <Video
          src={staticFile("aroll-k.mp4")}
          style={{
            position: "absolute", width: 1080, height: 1920, transformOrigin: "0 0",
            left: w / 2 - fx * scale, top: h / 2 - fy * scale, transform: `scale(${scale})`,
          }}
        />
      </div>
    </div>
  );
};

const moveTransform = (move: string | undefined, q: number) => {
  switch (move) {
    case "in": return `scale(${1.02 + 0.08 * q})`;
    case "out": return `scale(${1.1 - 0.08 * q})`;
    case "left": return `scale(1.12) translateX(${30 - 60 * q}px)`;
    case "right": return `scale(1.12) translateX(${-30 + 60 * q}px)`;
    default: return "scale(1.04)";
  }
};

const Shot: React.FC<{ s: (typeof SHOTS)[number] }> = ({ s }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const len = (s.to - s.from) * fps;
  const q = interpolate(f, [0, len], [0, 1], { extrapolateRight: "clamp" });
  if (s.mg === "speed") return <SpeedCompare />;
  return (
    <AbsoluteFill style={{ transform: `scale(${s.zoom ?? 1})`, transformOrigin: s.pos ?? "50% 50%" }}>
      <AbsoluteFill style={{ transform: moveTransform(s.move, q) }}>
        <Video
          src={staticFile(`v/${s.vid}`)}
          muted
          trimBefore={Math.round((s.start ?? 0) * fps)}
          objectFit="cover"
          style={{ width: "100%", height: "100%" }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const appear = (t: number, at: number, d = 0.35) =>
  interpolate(t, [at, at + d], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });

// 「今天的我们才走到山脚」：真实山景上，山顶标 AGI，山脚亮起「我们在这」
const MountainTags: React.FC<{ t: number }> = ({ t }) => {
  const peak = appear(t, MOUNTAIN_TAGS.peakAt);
  const foot = appear(t, MOUNTAIN_TAGS.footAt);
  const tag = (op: number, style: React.CSSProperties, text: string, color: string) => (
    <div style={{
      position: "absolute", ...style, opacity: op, transform: `translateY(${(1 - op) * 20}px)`,
      padding: "8px 22px", background: "rgba(5,8,10,0.75)", border: `3px solid ${color}`,
      fontFamily: /[A-Z]/.test(text) ? "Orbitron" : "NotoSC", fontWeight: 900, fontSize: 54, color,
    }}>{text}</div>
  );
  return (
    <AbsoluteFill>
      {tag(peak, { left: 400, top: 40 }, "▲ AGI", "#fff")}
      <div style={{ position: "absolute", left: 140, top: 470, width: 30 * foot, height: 30 * foot, marginLeft: -15 * foot, marginTop: -15 * foot, borderRadius: "50%", background: LIME, boxShadow: `0 0 0 ${10 + 30 * (1 - foot)}px rgba(156,249,61,${0.35 * foot})` }} />
      {tag(foot, { left: 190, top: 420 }, "我们在这", LIME)}
    </AbsoluteFill>
  );
};

// 第三点：工业革命 vs AI，两行计数和进度条按口播滚动
const speedValue = (t: number, [a, b]: readonly [number, number], to: number) =>
  Math.round(interpolate(t, [a, b], [0, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.quad) }));

const SpeedCompare: React.FC = () => {
  const { fps } = useVideoConfig();
  const t = SPEED.from + useCurrentFrame() / fps;
  const rows = appear(t, SPEED.from, 0.25);
  const v1 = speedValue(t, SPEED.slow, 100);
  const v2 = speedValue(t, SPEED.fast, 10);
  const row = (y: number, label: string, v: number, max: number, color: string, suffix: string, rolling: boolean) => (
    <div style={{ position: "absolute", left: 60, top: y, width: 960, opacity: rows }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontFamily: "NotoSC", fontWeight: 900, fontSize: 52, color: "#fff", textShadow: "0 3px 12px rgba(0,0,0,0.9)" }}>{label}</div>
        <div style={{ fontFamily: "Orbitron", fontWeight: 900, fontSize: 96, color, fontVariantNumeric: "tabular-nums", textShadow: "0 4px 16px rgba(0,0,0,0.9)", filter: rolling ? "blur(1px)" : undefined }}>
          {v}<span style={{ fontFamily: "NotoSC", fontSize: 48, marginLeft: 8 }}>{suffix}</span>
        </div>
      </div>
      <div style={{ marginTop: 10, height: 40, background: "rgba(255,255,255,0.15)", borderRadius: 6, position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${(v / max) * 100}%`, background: color, borderRadius: 6 }} />
      </div>
    </div>
  );
  return (
    <AbsoluteFill>
      <Video src={staticFile(`v/${SPEED.bg}`)} muted trimBefore={Math.round(SPEED.bgStart * fps)} objectFit="cover" style={{ width: "100%", height: "100%" }} />
      <AbsoluteFill style={{ background: "rgba(0,0,0,0.6)" }} />
      {row(120, "工业革命", v1, 100, "rgba(230,234,240,0.95)", v1 >= 100 ? "+ 年" : "年", t > SPEED.slow[0] && t < SPEED.slow[1])}
      {row(350, "AI", v2, 100, LIME, "年", t > SPEED.fast[0] && t < SPEED.fast[1])}
    </AbsoluteFill>
  );
};

// 第六点：两道线按词画出
const TwoLines: React.FC<{ t: number }> = ({ t }) => {
  const l1 = appear(t, TWO_LINES.line1.at, 0.45);
  const tag = appear(t, TWO_LINES.line1.tagAt, 0.25);
  const l2 = appear(t, TWO_LINES.line2.at, 0.45);
  const line = (y: number, p: number, color: string, text: string) => (
    <div style={{ position: "absolute", left: 0, top: y, width: 1080 }}>
      <div style={{ height: 6, width: `${p * 100}%`, background: color, boxShadow: "0 2px 10px rgba(0,0,0,0.6)" }} />
      <div style={{
        marginTop: 12, marginLeft: 36, display: "inline-block", opacity: p, padding: "8px 18px", background: "rgba(5,8,10,0.8)",
        fontFamily: "NotoSC", fontWeight: 900, fontSize: 44, color: "#fff",
      }}>{text}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `rgba(0,0,0,${0.35 * l1})` }} />
      {line(150, l1, "#fff", TWO_LINES.line1.text)}
      <div style={{
        position: "absolute", right: 40, top: 178, opacity: tag, transform: `scale(${interpolate(tag, [0, 1], [1.4, 1])})`,
        padding: "6px 18px", border: `4px solid ${LIME}`, fontFamily: "NotoSC", fontWeight: 900, fontSize: 40, color: LIME, background: "rgba(5,8,10,0.8)",
      }}>{TWO_LINES.line1.tag}</div>
      {line(370, l2, "#ff4d4d", TWO_LINES.line2.text)}
    </AbsoluteFill>
  );
};

const Band: React.FC<{ t: number }> = ({ t }) => {
  const { fps } = useVideoConfig();
  const p = pipProgress(t);
  // 圆镜收到一半时素材带才出来，回大人像时先退
  const vis = interpolate(p, [0.35, 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (vis <= 0) return null;
  const chapter = [...CHAPTERS].reverse().find((c) => t >= c.at);
  const hits = [...CHAPTERS.map((c) => c.at), ...IMPACTS];
  const flash = hits.map((at) => interpolate(t, [at - 0.03, at, at + 0.2], [0, 0.85, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))
    .reduce((a, b) => Math.max(a, b), 0);
  // 冲击点震动：0.4 秒内衰减
  const shake = IMPACTS.map((at) => {
    const d = t - at;
    if (d < 0 || d > 0.4) return [0, 0];
    const k = (1 - d / 0.4) * 22;
    return [Math.sin(d * 95) * k, Math.cos(d * 77) * k * 0.7];
  }).reduce((a, b) => [a[0] + b[0], a[1] + b[1]], [0, 0]);
  return (
    <div style={{
      position: "absolute", left: 0, top: BAND.top, width: 1080, height: BAND.h, overflow: "hidden",
      opacity: vis, transform: `translate(${shake[0]}px, ${(1 - vis) * 40 + shake[1]}px)`,
    }}>
      {SHOTS.map((s, i) => (
        <Sequence key={i} from={Math.round(s.from * fps)} durationInFrames={Math.round((s.to - s.from) * fps)} layout="none">
          <AbsoluteFill><Shot s={s} /></AbsoluteFill>
        </Sequence>
      ))}
      {t >= TWO_LINES.from && t < TWO_LINES.to && <TwoLines t={t} />}
      {t >= MOUNTAIN_TAGS.from && t < MOUNTAIN_TAGS.to && <MountainTags t={t} />}
      {chapter && <ChapterTag n={chapter.n} t={t - chapter.at} />}
      {LABELS.filter((l) => t >= l.from && t < l.to).map((l) => <NameLabel key={l.main} l={l} t={t} />)}
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </div>
  );
};

const ChapterTag: React.FC<{ n: number; t: number }> = ({ n, t }) => {
  const x = interpolate(t, [0, 0.35], [-220, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.6)) });
  return (
    <div style={{
      position: "absolute", left: 28 + x, top: 26, padding: "8px 20px", borderRadius: 999,
      background: "rgba(10,14,18,0.78)", border: "2px solid rgba(255,255,255,0.85)",
      fontFamily: "NotoSC", fontWeight: 700, fontSize: 34, color: "#fff", letterSpacing: 2,
    }}>
      第 {n} 个<span style={{ color: LIME, marginLeft: 10 }}>{n}/7</span>
    </div>
  );
};

const NameLabel: React.FC<{ l: (typeof LABELS)[number]; t: number }> = ({ l, t }) => {
  const p = interpolate(t - l.from, [0, 0.3], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const out = interpolate(t, [l.to - 0.15, l.to], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 40, bottom: 40, opacity: out, display: "flex", alignItems: "stretch" }}>
      <div style={{ width: 8, background: LIME, boxShadow: `0 0 16px ${LIME}`, transform: `scaleY(${p})` }} />
      <div style={{
        clipPath: `inset(0 ${100 - p * 100}% 0 0)`, background: "rgba(6,10,12,0.78)", padding: "12px 26px 14px 20px",
        borderTop: "1px solid rgba(156,249,61,0.5)", borderBottom: "1px solid rgba(156,249,61,0.5)",
      }}>
        <div style={{ fontFamily: "NotoSC", fontWeight: 800, fontSize: 46, color: "#fff", letterSpacing: 2 }}>{l.main}</div>
        <div style={{ fontFamily: "Orbitron", fontWeight: 600, fontSize: 24, color: LIME, letterSpacing: 4, marginTop: 4, textTransform: "uppercase" }}>{l.sub}</div>
      </div>
    </div>
  );
};

// 拉丁字母和数字用 Orbitron，汉字用思源黑体 900
const isHan = (c: string) => /[一-鿿]/.test(c);
const TechChar: React.FC<{ c: string; size: number; color: string }> = ({ c, size, color }) => (
  <span style={{ fontFamily: isHan(c) ? "NotoSC" : "Orbitron", fontWeight: 900, fontSize: isHan(c) ? size * 0.92 : size, color }}>{c}</span>
);

// 花字时间表：逐字出现时刻、数字翻滚的每次跳字、落定时刻。画面和音效共用这一份
const ROLL = 0.65;
const CHAR_GAP = 0.07;
type FlowerPlan = { textAt: number[]; ticks: number[]; lockAt: number | null; suffixAt: number[] };
const planFlower = (fl: (typeof FLOWERS)[number], fps: number): FlowerPlan => {
  const textChars = [...(fl.text ?? "")];
  const textAt = textChars.map((_, i) => i * CHAR_GAP);
  const afterText = textChars.length ? textChars.length * CHAR_GAP : 0;
  const ticks: number[] = [];
  let lockAt: number | null = null;
  if (fl.roll) {
    let last = NaN;
    for (let f = 0; f < ROLL * fps; f++) {
      const v = rollValue(fl, afterText, afterText + f / fps);
      if (v !== last) ticks.push(afterText + f / fps);
      last = v;
    }
    lockAt = afterText + ROLL;
  }
  const sufStart = fl.roll ? (lockAt as number) + 0.08 : afterText;
  const suffixAt: number[] = [];
  let k = 0;
  for (const c of [...(fl.suffix ?? "")]) {
    suffixAt.push(c === " " ? -1 : sufStart + k * CHAR_GAP);
    if (c !== " ") k++;
  }
  return { textAt, ticks, lockAt, suffixAt };
};
const rollValue = (fl: (typeof FLOWERS)[number], start: number, local: number) => {
  if (!fl.roll) return 0;
  const p = interpolate(local - start, [0, ROLL], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return Math.round(fl.roll.start + (fl.roll.value - fl.roll.start) * p);
};

// 单个字落下：放大落定，无发光
const charPop = (local: number, at: number, fps: number) => {
  if (at < 0) return 1;
  const sp = spring({ frame: (local - at) * fps, fps, config: { damping: 11, stiffness: 260, mass: 0.5 } });
  return local < at ? 0 : sp;
};

const FlowerText: React.FC<{ fl: (typeof FLOWERS)[number]; t: number }> = ({ fl, t }) => {
  const { fps } = useVideoConfig();
  const local = t - fl.from;
  const plan = planFlower(fl, fps);
  const out = interpolate(t, [fl.to - 0.2, fl.to], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const afterText = plan.textAt.length * CHAR_GAP;
  const rolling = fl.roll && plan.lockAt !== null && local >= afterText && local < plan.lockAt;
  const num = fl.roll && local >= afterText ? rollValue(fl, afterText, local) : null;
  const lockPop = plan.lockAt !== null ? charPop(local, plan.lockAt, fps) : 1;
  const corner = interpolate(local, [0, 0.3], [40, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const cornerOp = interpolate(local, [0, 0.12], [0, 1], { extrapolateRight: "clamp" });
  const shadow = "0 4px 14px rgba(0,0,0,0.85), 0 1px 3px rgba(0,0,0,0.9)";
  const units = [...(fl.text ?? "") + (fl.roll ? String(fl.roll.value) : "") + (fl.suffix ?? "")].reduce((n, c) => n + (isHan(c) ? 1 : 0.72), 0);
  const size = Math.min(136, 860 / units);
  const line = `5px solid ${LIME}`;
  // 结尾回到大人像后，花字放到胸前
  const portrait = t >= PIP.growAt;
  const one = (c: string, at: number, key: string, sz: number, color: string) => {
    const p = charPop(local, at, fps);
    return (
      <span key={key} style={{ display: "inline-block", opacity: Math.min(p * 1.5, 1), transform: `scale(${interpolate(p, [0, 1], [1.5, 1])})` }}>
        {c === " " ? " " : <TechChar c={c} size={sz} color={color} />}
      </span>
    );
  };
  return (
    <div style={{
      position: "absolute", left: 0, width: 1080, top: portrait ? 900 : BAND.top, height: BAND.h,
      display: "flex", alignItems: "center", justifyContent: "center", opacity: out,
      background: `radial-gradient(45% 38% at 50% 50%, rgba(0,0,0,${0.55 * cornerOp}) 0%, rgba(0,0,0,0) 100%)`,
    }}>
      <div style={{ position: "relative", padding: "26px 54px" }}>
        {[["top", "left"], ["top", "right"], ["bottom", "left"], ["bottom", "right"]].map(([v, h]) => (
          <div key={v + h} style={{
            position: "absolute", width: 44, height: 44, [v]: -corner, [h]: -corner, opacity: cornerOp,
            [`border${v[0].toUpperCase() + v.slice(1)}`]: line, [`border${h[0].toUpperCase() + h.slice(1)}`]: line,
          } as React.CSSProperties} />
        ))}
        <div style={{ display: "flex", alignItems: "baseline", gap: 14, textShadow: shadow, whiteSpace: "nowrap" }}>
          {fl.text && <span>{[...fl.text].map((c, i) => one(c, plan.textAt[i], "t" + i, size, "#fff"))}</span>}
          {num !== null && (
            <span style={{
              display: "inline-block", fontVariantNumeric: "tabular-nums", filter: rolling ? "blur(1.2px)" : undefined,
              transform: rolling ? `translateY(${Math.sin(local * 60) * 5}px)` : `scale(${interpolate(lockPop, [0, 1], [1.12, 1])})`,
            }}>
              {[...String(num)].map((c, i) => <TechChar key={i} c={c} size={size} color="#fff" />)}
            </span>
          )}
          {fl.suffix && (
            <span>{[...fl.suffix].map((c, i) => one(c, plan.suffixAt[i], "s" + i, size * 0.62, fl.roll ? LIME : "#fff"))}</span>
          )}
        </div>
      </div>
    </div>
  );
};

// 音效：花字逐字 blip、数字翻滚 tick、落定 lock、冲击 bass、章节 sweep、人物标签 data
const SfxLayer: React.FC = () => {
  const { fps } = useVideoConfig();
  const ev: { at: number; src: string; vol: number }[] = [];
  for (const fl of FLOWERS) {
    const plan = planFlower(fl, fps);
    plan.textAt.forEach((a) => ev.push({ at: fl.from + a, src: "sfx/blip.wav", vol: 0.16 }));
    plan.ticks.forEach((a) => ev.push({ at: fl.from + a, src: "sfx/tick.wav", vol: 0.14 }));
    if (plan.lockAt !== null) ev.push({ at: fl.from + plan.lockAt, src: "sfx/lock.wav", vol: 0.2 });
    plan.suffixAt.filter((a) => a >= 0).forEach((a) => ev.push({ at: fl.from + a, src: "sfx/blip.wav", vol: 0.14 }));
  }
  IMPACTS.forEach((a) => ev.push({ at: a - 0.08, src: "sfx/bass-hit-short.wav", vol: 0.4 }));
  CHAPTERS.forEach((c) => ev.push({ at: c.at - 0.3, src: "sfx/sweep-scifi-fast.wav", vol: 0.22 }));
  LABELS.forEach((l) => ev.push({ at: l.from, src: "sfx/data.wav", vol: 0.12 }));
  ([[SPEED.slow, 100], [SPEED.fast, 10]] as const).forEach(([range, to]) => {
    let last = -1;
    for (let f = Math.round(range[0] * fps); f <= Math.round(range[1] * fps); f++) {
      const v = speedValue(f / fps, range, to);
      if (v !== last && v > 0) ev.push({ at: f / fps, src: "sfx/tick.wav", vol: 0.14 });
      last = v;
    }
    ev.push({ at: range[1], src: "sfx/lock.wav", vol: 0.2 });
  });
  const extra = { blip: ["sfx/blip.wav", 0.16], lock: ["sfx/lock.wav", 0.2], data: ["sfx/data.wav", 0.12], sweep: ["sfx/sweep-scifi-fast.wav", 0.2] } as const;
  EXTRA_SFX.forEach((e) => ev.push({ at: e.kind === "sweep" ? e.at - 0.3 : e.at, src: extra[e.kind][0], vol: extra[e.kind][1] }));
  return (
    <>
      {ev.map((e, i) => (
        <Sequence key={i} from={Math.max(0, Math.round(e.at * fps))} durationInFrames={Math.round(1.3 * fps)} layout="none">
          <Audio src={staticFile(e.src)} volume={e.vol * SFX_GAIN} />
        </Sequence>
      ))}
    </>
  );
};

const units = (s: string) => [...s].reduce((n, c) => n + (/[\u0000-ÿ]/.test(c) ? 0.55 : 1), 0);

const Caption: React.FC<{ t: number }> = ({ t }) => {
  // 句间空隙小于 0.4 秒时延到下一句，避免字幕闪断
  const cue = CUES.find((c, i) => {
    const next = CUES[i + 1];
    const end = next && next.from - c.to < 0.4 ? next.from : c.to;
    return t >= c.from && t < end;
  });
  if (!cue) return null;
  const p = pipProgress(t);
  const top = lerp(1500, BAND.top + BAND.h + BAND.h * 0.1, p);
  // 得意黑字面偏窄，按每个汉字约 0.9em 估宽
  const size = Math.min(68, 980 / (units(cue.text) * 0.9));
  const enSize = Math.min(44, 980 / ([...cue.en].length * 0.5));
  const shadow = "0 3px 10px rgba(0,0,0,0.85), 0 0 3px rgba(0,0,0,0.95)";
  return (
    <div style={{ position: "absolute", left: 0, width: 1080, top, textAlign: "center", color: "#fff", textShadow: shadow }}>
      <div style={{ fontFamily: "Smiley", fontSize: size, lineHeight: 1.2, whiteSpace: "nowrap" }}>{cue.text}</div>
      <div style={{ fontFamily: "Arial, sans-serif", fontStyle: "italic", fontSize: enSize, lineHeight: 1.25, whiteSpace: "nowrap", marginTop: 6 }}>{cue.en}</div>
    </div>
  );
};

const Title: React.FC = () => (
  <div style={{ position: "absolute", left: 0, width: 1080, top: 150, textAlign: "center", fontFamily: "NotoSC", fontWeight: 700 }}>
    <div style={{ transform: "skewX(-12deg)", color: "#fff", fontSize: 78, letterSpacing: 2.5, lineHeight: 1.2 }}>{TITLE.line1}</div>
    <div style={{ transform: "skewX(-12deg)", fontSize: 82, letterSpacing: 2.5, lineHeight: 1.2, marginTop: 8, ...titleLine2Style() }}>{TITLE.line2}</div>
  </div>
);

const titleLine2Style = (): React.CSSProperties => {
  switch (LOOK.title) {
    case "cyan": return { color: CYAN };
    case "amber": return { color: "#FFB547" };
    case "gradient": return { backgroundImage: `linear-gradient(90deg, ${LIME}, ${CYAN})`, WebkitBackgroundClip: "text", color: "transparent" };
    default: return { color: LIME };
  }
};

// 账号名：标题下方一行小字，或右上角小角标；都压低透明度，不抢标题
const Watermark: React.FC = () => {
  if (LOOK.mark === "none") return null;
  const base: React.CSSProperties = { position: "absolute", fontFamily: "NotoSC", fontWeight: 600, color: "rgba(255,255,255,0.55)", letterSpacing: 3 };
  if (LOOK.mark === "corner") {
    return <div style={{ ...base, right: 36, top: 70, fontSize: 26, padding: "4px 12px", border: "1px solid rgba(255,255,255,0.3)", borderRadius: 999 }}>@贝拉的科技手记</div>;
  }
  return <div style={{ ...base, left: 0, width: 1080, top: 372, textAlign: "center", fontSize: 28 }}>— @贝拉的科技手记 —</div>;
};

// 银灰透视网格：左上远层慢移，右下近层移动和缩放更大，中间留暗
const GridPlane: React.FC<{ t: number; corner: "tl" | "br"; color?: string }> = ({ t, corner, color }) => {
  const near = corner === "br";
  const cell = near ? 110 : 90;
  const shift = (t * (near ? 34 : 18)) % cell;
  const breathe = near ? 1 + 0.04 * Math.sin(t * 0.35) : 1 + 0.015 * Math.sin(t * 0.25);
  const line = color ?? "rgba(222,226,234,0.85)";
  return (
    <div style={{
      position: "absolute", width: 1600, height: 1600,
      left: near ? 150 : -650, top: near ? 820 : -500,
      perspective: 900,
      WebkitMaskImage: near
        ? "linear-gradient(300deg, #000 35%, transparent 62%)"
        : "linear-gradient(120deg, #000 35%, transparent 62%)",
    }}>
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `linear-gradient(${line} 2px, transparent 2px), linear-gradient(90deg, ${line} 2px, transparent 2px)`,
        backgroundSize: `${cell}px ${cell}px`,
        backgroundPosition: `${shift}px ${shift}px`,
        transform: `${near ? "rotateY(-50deg) rotateX(18deg) rotateZ(-20deg)" : "rotateY(50deg) rotateX(-18deg) rotateZ(-20deg)"} scale(${breathe})`,
      }} />
    </div>
  );
};

const DiagGrid: React.FC<{ t: number; brand?: boolean }> = ({ t, brand }) => (
  <>
    <GridPlane t={t} corner="tl" color={brand ? "rgba(156,249,61,0.8)" : undefined} />
    <GridPlane t={t} corner="br" color={brand ? "rgba(79,227,240,0.85)" : undefined} />
  </>
);

// 发光扫线：网格本身压暗，一团光沿对角方向慢慢扫过，只有光经过的线被点亮
const PulseGrid: React.FC<{ t: number }> = ({ t }) => {
  // 两团光分别在左上、右下网格上来回扫
  const k = (Math.sin(t * 0.9) + 1) / 2;
  const x1 = 40 + 460 * k, y1 = 60 + 300 * k;
  const x2 = 1040 - 460 * k, y2 = 1860 - 300 * k;
  return (
    <>
      <AbsoluteFill style={{ opacity: 0.45 }}><DiagGrid t={t} /></AbsoluteFill>
      <AbsoluteFill style={{
        WebkitMaskImage: `radial-gradient(360px 360px at ${x1}px ${y1}px, #000 0%, transparent 70%), radial-gradient(360px 360px at ${x2}px ${y2}px, #000 0%, transparent 70%)`,
        filter: `drop-shadow(0 0 6px ${LIME})`,
      }}>
        <DiagGrid t={t} />
      </AbsoluteFill>
    </>
  );
};

// 宇宙感：远处星点缓慢漂移闪烁，底部一块弯曲的透视地平网格
const Cosmos: React.FC<{ t: number }> = ({ t }) => {
  const stars = React.useMemo(() => Array.from({ length: 220 }, (_, i) => {
    const r = (n: number) => { const v = Math.sin(i * 12.9898 + n * 78.233) * 43758.5453; return v - Math.floor(v); };
    return { x: r(1) * 1080, y: r(2) * 1920, s: 1 + r(3) * 2.5, ph: r(4) * 6.28, sp: 4 + r(5) * 10 };
  }), []);
  const shift = (t * 40) % 80;
  return (
    <>
      <AbsoluteFill style={{ background: "radial-gradient(90% 60% at 50% 40%, #0b1424 0%, #04060b 70%)" }} />
      {stars.map((st, i) => (
        <div key={i} style={{ position: "absolute", left: st.x, top: (st.y + t * st.sp) % 1920, width: st.s, height: st.s, borderRadius: "50%", background: "#fff", opacity: 0.25 + 0.5 * (0.5 + 0.5 * Math.sin(t * 1.5 + st.ph)) }} />
      ))}
      <div style={{ position: "absolute", left: -600, width: 2280, top: 1180, height: 900, perspective: 500, WebkitMaskImage: "linear-gradient(180deg, transparent 0%, #000 25%)" }}>
        <div style={{
          position: "absolute", inset: 0, transform: "rotateX(72deg)", transformOrigin: "50% 0%",
          backgroundImage: "linear-gradient(rgba(170,200,255,0.55) 2px, transparent 2px), linear-gradient(90deg, rgba(170,200,255,0.55) 2px, transparent 2px)",
          backgroundSize: "80px 80px", backgroundPosition: `0 ${shift}px`,
        }} />
      </div>
    </>
  );
};

// 三角网格：0°/60°/120° 三组线交错，没有直角方格，缓慢平移
const TriGrid: React.FC<{ t: number }> = ({ t }) => {
  const line = "rgba(210,216,226,0.5)";
  const d = (t * 14) % 100;
  const set = (deg: number) => `repeating-linear-gradient(${deg}deg, ${line} 0 2px, transparent 2px 100px)`;
  return (
    <AbsoluteFill style={{
      backgroundImage: `${set(0)}, ${set(60)}, ${set(120)}`, backgroundPosition: `${d}px ${d * 0.6}px`,
      WebkitMaskImage: "radial-gradient(70% 55% at 50% 50%, transparent 35%, #000 85%)",
    }} />
  );
};

const Background: React.FC<{ t: number }> = ({ t }) => (
  <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
    {/* brand：网格换成主题色，左上青柠绿、右下青色 */}
    {LOOK.bg === "cosmos" ? <Cosmos t={t} /> : LOOK.bg === "tri" ? <TriGrid t={t} /> : LOOK.bg === "pulse" ? <PulseGrid t={t} /> : <DiagGrid t={t} brand={LOOK.bg === "brand"} />}
    <AbsoluteFill style={{ background: "radial-gradient(55% 40% at 50% 50%, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%)" }} />
  </AbsoluteFill>
);

export const Main: React.FC = () => {
  const [fontHandle] = React.useState(() => delayRender("fonts"));
  React.useEffect(() => {
    fontsReady.then(() => continueRender(fontHandle), (e) => cancelRender(e));
  }, [fontHandle]);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const p = pipProgress(t);
  return (
    <AbsoluteFill>
      <Background t={t} />
      <ARoll t={t} />
      {/* 大人像阶段给标题压一层渐变 */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 26%)", opacity: 1 - p }} />
      <Band t={t} />
      <Title />
      <Watermark />
      {FLOWERS.filter((fl) => t >= fl.from && t < fl.to).map((fl) => (
        <FlowerText key={fl.from} fl={fl} t={t} />
      ))}
      <Caption t={t} />
      <SfxLayer />
    </AbsoluteFill>
  );
};
