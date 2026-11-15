// 所有时间都是粗剪.mp4（1.2× 后）的成片秒数
// 节奏规则（用户 2026-11-02）：素材 2–3 秒换一次；不换素材时必须有花字或音效制造变化
export const FPS = 30;
export const TOTAL_SECONDS = 149.1;

export const TITLE = { line1: "哈萨比斯的七个 AGI 判断", line2: "离普通人到底还有多远" };

// 大人像 → 小圆镜 → 结尾放大回大人像
export const PIP = { shrinkAt: 2.1, growAt: 138.32, dur: 0.4 };
// 结尾大人像阶段的推近节点：每到一个点在 1.0 / 1.1 倍之间切换
export const PUNCH_INS = [140.18, 142.9, 144.88, 146.68];

// 全部用真实视频（用户 2026-11-02：不要静态图片）。vid 是 public/v/ 下的文件名，start 是该文件内的入点秒数
// yt_DsewHeVbL-0_* 斯坦福 GSB 对话 / yt_YtPaZsasmNA_* 诺贝尔讲座 / yt_d95J8yzvjbQ_* 纪录片 The Thinking Game / mk* Mixkit 实拍
export type Shot = {
  from: number; to: number;
  vid?: string; start?: number; mg?: "speed";
  zoom?: number; pos?: string; move?: "in" | "out" | "left" | "right";
};
export const SHOTS: Shot[] = [
  { from: 2.1, to: 3.0, vid: "yt_YtPaZsasmNA_178.mp4", start: 2.0, zoom: 1.35, pos: "50% 20%", move: "in" }, // 诺贝尔讲座本人
  { from: 3.0, to: 4.6, vid: "yt_DsewHeVbL-0_3178.mp4", start: 1.0, move: "in" }, // 斯坦福近景
  { from: 4.6, to: 6.06, vid: "yt_DsewHeVbL-0_778.mp4", start: 0.3, move: "out" }, // 斯坦福全景
  { from: 6.06, to: 7.98, vid: "yt_DsewHeVbL-0_298.mp4", start: 0.5, move: "in" }, // 满场观众
  { from: 7.98, to: 10.15, vid: "yt_d95J8yzvjbQ_1158.mp4", start: 0.0, move: "in" }, // AlphaGo 对李世石大屏
  { from: 10.15, to: 11.54, vid: "yt_d95J8yzvjbQ_1118.mp4", start: 1.0, move: "in" }, // AlphaGo 团队
  { from: 11.54, to: 14.24, vid: "mk49878.mp4", start: 0, move: "out" }, // 城市夜景航拍
  { from: 14.24, to: 17.14, vid: "yt_DsewHeVbL-0_1258.mp4", start: 1.0, move: "in" }, // 哈萨比斯近景
  { from: 17.14, to: 19.94, vid: "mk28897.mp4", start: 0, move: "in" }, // 时钟
  { from: 19.94, to: 22.58, vid: "yt_d95J8yzvjbQ_2918.mp4", start: 0.5, move: "in" }, // DeepMind 实验室
  { from: 22.58, to: 23.92, vid: "mk21921.mp4", start: 1, move: "in" }, // 人形机器人
  { from: 23.92, to: 26.08, vid: "mk28901.mp4", start: 0, move: "in" }, // 沙漏
  { from: 26.08, to: 28.0, vid: "mk51689.mp4", start: 0, move: "in" }, // 雪山航拍
  { from: 28.0, to: 30.0, vid: "mk4132.mp4", start: 2, move: "out" }, // 山谷
  { from: 30.0, to: 32.08, vid: "mk4437.mp4", start: 0, move: "in" }, // 街头人群
  { from: 32.08, to: 34.08, vid: "yt_d95J8yzvjbQ_2878.mp4", start: 1.5, move: "in" }, // 实验室屏幕
  { from: 34.08, to: 35.8, vid: "mk41638.mp4", start: 0, move: "in" }, // 上班族看手机
  { from: 35.8, to: 37.76, vid: "mk4401.mp4", start: 0, move: "out" }, // 路口人潮
  { from: 37.76, to: 40.44, vid: "mk41174.mp4", start: 0, move: "in" }, // 用手机的人
  { from: 40.44, to: 42.1, vid: "mk4915.mp4", start: 0, move: "in" }, // 手机特写
  { from: 42.1, to: 44.04, vid: "mk43270.mp4", start: 0, move: "in" }, // 打字的人
  { from: 44.04, to: 45.52, vid: "mk49939.mp4", start: 0, move: "out" }, // 聊天的人
  { from: 45.52, to: 48.3, vid: "mk12913.mp4", start: 0, move: "in" }, // 医生问诊
  { from: 48.3, to: 50.38, vid: "mk11850.mp4", start: 0, move: "in" }, // 医生看片
  { from: 50.38, to: 53.42, vid: "mk47214.mp4", start: 0, move: "left" }, // 看盘
  { from: 53.42, to: 54.56, vid: "mk4789.mp4", start: 0, move: "in" }, // 孩子写作业
  { from: 54.56, to: 57.02, vid: "mk5722.mp4", start: 0, move: "in" }, // 妈妈辅导
  { from: 57.02, to: 58.38, vid: "mk5722.mp4", start: 4, zoom: 1.4, pos: "60% 40%", move: "out" }, // 辅导近景
  { from: 58.38, to: 59.58, vid: "mk17540.mp4", start: 0, move: "in" }, // 医生开处方
  { from: 59.58, to: 61.04, vid: "mk9607.mp4", start: 0, move: "in" }, // 行情屏
  { from: 61.04, to: 62.26, vid: "mk49845.mp4", start: 0, move: "in" }, // 城市
  { from: 62.26, to: 64.2, vid: "mk18296.mp4", start: 0, move: "in" }, // 数钱
  { from: 64.2, to: 65.74, vid: "mk21629.mp4", start: 0, move: "in" }, // 办公桌前的人
  { from: 65.74, to: 67.52, vid: "mk28616.mp4", start: 0, move: "in" }, // 快速人流
  { from: 67.52, to: 69.8, vid: "mk14051.mp4", start: 0, move: "in" }, // 工厂烟囱
  { from: 69.8, to: 72.34, vid: "mk17675.mp4", start: 0, move: "in" }, // 机器运转
  { from: 72.34, to: 74.2, vid: "yt_DsewHeVbL-0_3178.mp4", start: 4.0, zoom: 1.2, pos: "50% 30%", move: "in" }, // 哈萨比斯
  { from: 74.2, to: 77.28, mg: "speed" },
  { from: 77.28, to: 79.5, vid: "mk14631.mp4", start: 0, move: "out" }, // 工厂俯拍
  { from: 79.5, to: 81.48, vid: "yt_DsewHeVbL-0_2878.mp4", start: 0.5, move: "in" }, // 哈萨比斯
  { from: 81.48, to: 83.86, vid: "mk4401.mp4", start: 6, zoom: 1.3, move: "left" }, // 人潮
  { from: 83.86, to: 85.48, vid: "mk45676.mp4", start: 0, move: "in" }, // 篝火
  { from: 85.48, to: 87.4, vid: "mk1243.mp4", start: 0, move: "in" }, // 柴火
  { from: 87.4, to: 90, vid: "mk49846.mp4", start: 0, move: "out" }, // 城市灯火
  { from: 90, to: 92.22, vid: "mk20961.mp4", start: 0, move: "in" }, // 机器人眼睛
  { from: 92.22, to: 93.7, vid: "mk45220.mp4", start: 0, move: "in" }, // 机器人行走
  { from: 93.7, to: 95.3, vid: "mk23219.mp4", start: 0, move: "in" }, // 数据中心
  { from: 95.3, to: 97.58, vid: "yt_d95J8yzvjbQ_38.mp4", start: 3.45, move: "in" }, // 哈萨比斯（纪录片）
  { from: 97.58, to: 99.7, vid: "yt_d95J8yzvjbQ_558.mp4", start: 1.0, move: "in" }, // DeepMind 玩 Atari
  { from: 99.7, to: 101.82, vid: "yt_d95J8yzvjbQ_1878.mp4", start: 0.5, move: "in" }, // 盯着电脑的人
  { from: 101.82, to: 104.16, vid: "yt_d95J8yzvjbQ_678.mp4", start: 0.3, move: "in" }, // Atari 比分
  { from: 104.16, to: 107.74, vid: "yt_DsewHeVbL-0_1498.mp4", start: 0.5, move: "in" }, // 哈萨比斯
  { from: 107.74, to: 111.28, vid: "yt_d95J8yzvjbQ_998.mp4", start: 0.7, move: "left" }, // 机房里的人
  { from: 111.28, to: 113.86, vid: "mk47258.mp4", start: 0, move: "in" }, // 机械臂
  { from: 113.86, to: 114.94, vid: "yt_DsewHeVbL-0_2218.mp4", start: 0.0, move: "in" }, // 斯坦福全景
  { from: 114.94, to: 117.16, vid: "yt_d95J8yzvjbQ_3918.mp4", start: 1.0, move: "in" }, // 白板讨论
  { from: 117.16, to: 118.46, vid: "yt_DsewHeVbL-0_1258.mp4", start: 5.0, move: "in" }, // 哈萨比斯
  { from: 118.46, to: 120.82, vid: "yt_d95J8yzvjbQ_2198.mp4", start: 1.4, move: "out" }, // 观众看大屏
  { from: 120.82, to: 122.7, vid: "yt_d95J8yzvjbQ_4518.mp4", start: 0.3, move: "in" }, // 公司开会
  { from: 122.7, to: 125.64, vid: "mk49845.mp4", start: 6, move: "out" }, // 城市
  { from: 125.64, to: 127.98, vid: "mk41120.mp4", start: 0, move: "in" }, // 切蛋糕
  { from: 127.98, to: 129.9, vid: "mk47005.mp4", start: 0, move: "in" }, // 成堆现金
  { from: 129.9, to: 131.44, vid: "mk18305.mp4", start: 0, move: "in" }, // 钞票落下
  { from: 131.44, to: 133.24, vid: "mk41124.mp4", start: 0, move: "in" }, // 旋转蛋糕
  { from: 133.24, to: 135.52, vid: "mk47796.mp4", start: 0, move: "left" }, // 行情数据
  { from: 135.52, to: 136.52, vid: "mk4231.mp4", start: 0, move: "in" }, // 街头行人
  { from: 136.52, to: 138.42, vid: "mk4396.mp4", start: 0, move: "out" }, // 雪山云雾
];

// 第一点「山脚」：真实山景上标出山顶 AGI 和山脚「我们在这」
export const MOUNTAIN_TAGS = { from: 26.08, to: 30.0, peakAt: 27.3, footAt: 28.7 };

// 章节小标与转场
export const CHAPTERS = [
  { at: 14.24, n: 1 }, { at: 30.0, n: 2 }, { at: 67.52, n: 3 }, { at: 79.5, n: 4 },
  { at: 90, n: 5 }, { at: 104.16, n: 6 }, { at: 122.7, n: 7 },
];

// 冲击点：闪白 + 震动 + 低音
export const IMPACTS = [6.06, 69.8];

// 照片上的人物标签
export const LABELS = [
  { from: 2.14, to: 3.0, main: "2024 诺贝尔化学奖得主", sub: "Nobel Prize in Chemistry" },
  { from: 3.02, to: 6.0, main: "Demis Hassabis 哈萨比斯", sub: "Google DeepMind CEO" },
  { from: 95.3, to: 97.5, main: "哈萨比斯：不这么看", sub: "Demis Hassabis" },
];

// 科技感花字：roll 为数字翻滚（start → value），suffix 在翻滚落定后逐字弹出
// 结尾大人像阶段（growAt 之后）自动放到胸前位置
export type Flower = { from: number; to: number; text?: string; roll?: { start: number; value: number }; suffix?: string };
export const FLOWERS: Flower[] = [
  { from: 6.06, to: 7.9, text: "炸开了锅" },
  { from: 10.24, to: 11.5, roll: { start: 0, value: 7 }, suffix: "个判断" },
  { from: 17.38, to: 19.8, roll: { start: 1990, value: 2030 }, suffix: "± 1 年" },
  { from: 25.3, to: 26.05, text: "≈", roll: { start: 0, value: 4 }, suffix: "年" },
  { from: 36.4, to: 37.7, text: "超乎想象" },
  { from: 40.44, to: 42.05, text: "人手一个 AI" },
  { from: 48.9, to: 50.3, text: "问得更准" },
  { from: 51.12, to: 53.35, text: "风险 + 规则" },
  { from: 55.6, to: 56.95, text: "听懂为止" },
  { from: 57.02, to: 58.35, text: "它不替你拿主意" },
  { from: 62.26, to: 64.1, text: "学历？存款？" },
  { from: 64.2, to: 65.7, text: "会不会用 AI" },
  { from: 69.8, to: 72.3, text: "×", roll: { start: 1, value: 100 }, suffix: "倍" },
  { from: 72.34, to: 74.1, text: "还算保守" },
  { from: 81.48, to: 82.75, text: "SPECIES LEVEL" },
  { from: 85.9, to: 87.35, text: "学会用火" },
  { from: 90.66, to: 92.2, text: "智能 ≠ 意识" },
  { from: 100.1, to: 101.75, text: "没有意识" },
  { from: 117.16, to: 118.4, text: "先别迈" },
  { from: 119.1, to: 120.75, text: "所有人一起决定" },
  { from: 126.64, to: 127.92, text: "你多 = 我少" },
  { from: 129.9, to: 131.4, text: "够用的时代" },
  { from: 134.12, to: 135.5, text: "规则重写" },
  { from: 136.6, to: 137.32, text: "人活着图什么？" },
  { from: 141.08, to: 142.82, roll: { start: 2026, value: 2030 }, suffix: "等不到" },
  { from: 142.9, to: 144.02, text: "谁在用？" },
  { from: 144.06, to: 144.82, text: "谁在等？" },
  { from: 144.88, to: 146.62, text: "差距已经拉开" },
  { from: 147.32, to: 149.02, text: "评论区告诉我" },
];

// 自制段落内部元素出现时刻的音效
export const EXTRA_SFX: { at: number; kind: "blip" | "lock" | "data" | "sweep" }[] = [
  { at: 2.1, kind: "sweep" }, { at: 138.32, kind: "sweep" },
  { at: 26.3, kind: "data" }, { at: 27.3, kind: "blip" }, { at: 28.7, kind: "lock" },
  { at: 68.1, kind: "data" },
  { at: 105.88, kind: "data" }, { at: 109.5, kind: "lock" }, { at: 111.28, kind: "data" },
  ...PUNCH_INS.map((at) => ({ at, kind: "blip" as const })),
];

// 第三点速度对比：工业革命计数慢慢滚到 100+ 年，AI 一下跳到 10 年；底下是压暗的工厂实拍
export const SPEED = { from: 74.2, to: 77.28, bg: "mk14051.mp4", bgStart: 5, slow: [74.25, 75.6] as const, fast: [75.72, 76.02] as const };

// 第六点「两道线」叠层：在 L 齿轮红线素材上按词出现
export const TWO_LINES = {
  from: 104.16, to: 113.86,
  line1: { at: 105.88, text: "① 没有意识的强 AGI 工具", tagAt: 109.5, tag: "正在跨越" },
  line2: { at: 111.28, text: "② 有主观感受的 AI" },
};

// 口播字幕：中文在上，英文在下
export type Cue = { from: number; to: number; text: string; en: string };
export const CUES: Cue[] = [
  { from: 0.0, to: 2.1, text: "AGI 离我们到底还有多远？", en: "How far away is AGI, really?" },
  { from: 2.14, to: 3.8, text: "诺贝尔奖得主、DeepMind 掌门人", en: "Nobel laureate and head of DeepMind" },
  { from: 3.84, to: 6.0, text: "哈萨比斯前几天在斯坦福的一场对话", en: "Demis Hassabis's recent talk at Stanford" },
  { from: 6.06, to: 7.95, text: "直接把整个科技圈炸开了锅", en: "set the whole tech world on fire." },
  { from: 7.98, to: 10.2, text: "我把里面最颠覆认知、最超前的", en: "I've picked out the most mind-bending," },
  { from: 10.24, to: 11.5, text: "7 个判断挑了出来", en: "forward-looking 7 predictions." },
  { from: 11.54, to: 14.0, text: "看完你对未来的想法可能会彻底变掉", en: "They may totally change how you see the future." },
  { from: 14.24, to: 16.0, text: "第一个 也是最吓人的一个", en: "Number one, and the scariest:" },
  { from: 16.08, to: 17.1, text: "他直接给了时间", en: "he gave an actual date." },
  { from: 17.14, to: 19.7, text: "就在 2030 年前后 上下差不多一年", en: "Around 2030, give or take a year." },
  { from: 19.94, to: 22.5, text: "他说的 AGI 是认知能力上能跟人打平", en: "By AGI, he means systems as smart as humans" },
  { from: 22.58, to: 23.85, text: "甚至更强的系统", en: "or even smarter." },
  { from: 23.92, to: 25.95, text: "算下来离现在也就 4 年左右", en: "That's only about four years from now." },
  { from: 26.08, to: 27.62, text: "他还说 10 年后回头看", en: "He also said, looking back in ten years," },
  { from: 27.66, to: 29.9, text: "今天的我们其实才走到山脚", en: "we're only at the foot of the mountain today." },
  { from: 30.0, to: 32.08, text: "第二个 也是我觉得跟咱们关系最大的一个", en: "Number two: the one that matters most to us." },
  { from: 32.08, to: 34.08, text: "很多人会想 AGI 是实验室里的事", en: "Many think AGI is just a lab thing," },
  { from: 34.08, to: 35.8, text: "跟我上班工作有什么关系呢", en: "so what does it have to do with my job?" },
  { from: 35.8, to: 37.76, text: "答案是 关系大到超乎想象", en: "The answer: far more than you'd imagine." },
  { from: 37.76, to: 38.98, text: "因为以后每一个人身边", en: "Because soon, everyone" },
  { from: 38.98, to: 40.44, text: "大概率都会有一个自己的 AI", en: "will likely have an AI of their own," },
  { from: 40.44, to: 42.1, text: "就像现在人手一部手机", en: "just like everyone has a phone today." },
  { from: 42.1, to: 44.04, text: "你可以把它想成一个随叫随到", en: "Think of it as always on call," },
  { from: 44.04, to: 45.52, text: "从不嫌你问题多的帮手", en: "a helper that never tires of your questions." },
  { from: 45.52, to: 46.42, text: "身体不舒服", en: "Feeling unwell?" },
  { from: 46.42, to: 48.3, text: "它先帮你把症状和化验单理清楚", en: "It sorts out your symptoms and test results first," },
  { from: 48.3, to: 50.38, text: "你去见医生的时候呀 可以问得更准", en: "so you can ask your doctor better questions." },
  { from: 50.38, to: 51.12, text: "想理财", en: "Managing money?" },
  { from: 51.12, to: 53.42, text: "它把每个产品的风险和规则给你讲明白", en: "It explains each product's risks and rules." },
  { from: 53.42, to: 54.56, text: "孩子作业卡住了", en: "Kid stuck on homework?" },
  { from: 54.56, to: 55.6, text: "它能换着花样去讲", en: "It explains it in different ways" },
  { from: 55.6, to: 57.02, text: "讲到孩子听懂为止", en: "until your kid gets it." },
  { from: 57.02, to: 58.38, text: "当然 它不替你拿主意", en: "Of course, it won't decide for you." },
  { from: 58.38, to: 59.58, text: "看病还是要找医生", en: "You still need a doctor," },
  { from: 59.58, to: 61.04, text: "投资的风险还得自己担", en: "and investment risks are still yours." },
  { from: 61.04, to: 62.26, text: "但真到那一天", en: "But when that day comes," },
  { from: 62.26, to: 64.2, text: "人和人的差距不再是学历和存款", en: "the gap between people won't be degrees or savings," },
  { from: 64.2, to: 65.74, text: "而是你会不会用自己的 AI", en: "but whether you can use your own AI." },
  { from: 65.74, to: 67.52, text: "不会用的人 就会被甩得很远", en: "Those who can't will fall far behind." },
  { from: 67.52, to: 68.96, text: "第三个 是速度", en: "Number three: speed." },
  { from: 68.96, to: 69.8, text: "他的判断是", en: "His view:" },
  { from: 69.8, to: 72.34, text: "这次变化可能比工业革命快 100 倍", en: "this change may be 100x faster than the Industrial Revolution," },
  { from: 72.34, to: 74.2, text: "而且他觉得这还算保守了", en: "and he thinks that's conservative." },
  { from: 74.2, to: 75.68, text: "工业革命花了上百年", en: "The Industrial Revolution took over a century;" },
  { from: 75.68, to: 77.28, text: "AI 可能只要 10 年", en: "AI may take just ten years." },
  { from: 77.28, to: 79.5, text: "留给社会适应的时间很紧张", en: "Society has very little time to adapt." },
  { from: 79.5, to: 81.48, text: "第四个 他用了一个说法", en: "Number four: he used a phrase," },
  { from: 81.48, to: 82.8, text: "物种级转变", en: "Species Level Transition" },
  { from: 82.8, to: 83.86, text: "物种级的转变", en: "a species-level transition." },
  { from: 83.86, to: 84.48, text: "说白了", en: "Put simply," },
  { from: 84.48, to: 85.48, text: "AI 对人类的分量", en: "AI's weight for humanity" },
  { from: 85.48, to: 87.4, text: "可能跟当年学会用火差不多", en: "may be like learning to use fire," },
  { from: 87.4, to: 90, text: "是整个物种往前迈一大步的那种节点", en: "a moment when the whole species leaps forward." },
  { from: 90, to: 90.66, text: "第五个", en: "Number five:" },
  { from: 90.66, to: 92.22, text: "智能和意识可能是两回事", en: "intelligence and consciousness may be separate." },
  { from: 92.22, to: 95.3, text: "我们总觉得 越聪明的东西就越会有自我意识", en: "We assume smarter things become self-aware." },
  { from: 95.3, to: 96.36, text: "哈萨比斯不这么看", en: "Hassabis disagrees." },
  { from: 96.36, to: 97.58, text: "这两样能分开", en: "The two can be separated." },
  { from: 97.58, to: 98.64, text: "做一个聪明的系统", en: "A smart system" },
  { from: 98.64, to: 99.7, text: "没必要让它有意识", en: "doesn't need to be conscious." },
  { from: 99.7, to: 101.82, text: "现在的 AI 都没有意识", en: "Today's AI isn't conscious," },
  { from: 101.82, to: 104.16, text: "可很多事已经比人做得要好了", en: "yet they already beat humans at many tasks." },
  { from: 104.16, to: 104.9, text: "第六个", en: "Number six:" },
  { from: 104.9, to: 105.88, text: "他画了两道线", en: "he drew two lines." },
  { from: 105.88, to: 107.74, text: "第一道 是做出没有意识", en: "The first: AGI tools without consciousness" },
  { from: 107.74, to: 109.5, text: "但足够强的 AGI 工具", en: "but powerful enough." },
  { from: 109.5, to: 111.28, text: "这道线我们正在跨越", en: "We're crossing that line now." },
  { from: 111.28, to: 113.86, text: "第二道 是造出有主观感受的 AI", en: "The second: AI with subjective experience." },
  { from: 113.86, to: 114.94, text: "他的态度很明确", en: "His stance is clear:" },
  { from: 114.94, to: 117.16, text: "科学上还说不清意识是什么之前", en: "until science can define consciousness," },
  { from: 117.16, to: 118.46, text: "这一步不该迈", en: "we shouldn't take that step." },
  { from: 118.46, to: 120.82, text: "要不要迈 也该由所有人一起决定", en: "Whether to take it is for everyone to decide," },
  { from: 120.82, to: 122.7, text: "不该只有几家公司拍板", en: "not just a few companies." },
  { from: 122.7, to: 123.42, text: "第七个", en: "Number seven:" },
  { from: 123.42, to: 124.3, text: "看得更远一些", en: "looking further ahead." },
  { from: 124.3, to: 125.64, text: "现在的经济学有个前提", en: "Today's economics assumes" },
  { from: 125.64, to: 126.64, text: "东西不够分", en: "there isn't enough to go around:" },
  { from: 126.64, to: 127.98, text: "你多拿了 我就少拿", en: "if you get more, I get less." },
  { from: 127.98, to: 128.6, text: "他觉得", en: "He believes" },
  { from: 128.6, to: 129.9, text: "AI 可能会让人类第一次", en: "AI may, for the first time," },
  { from: 129.9, to: 131.44, text: "进入一个东西够用的时代", en: "bring us an age of enough." },
  { from: 131.44, to: 133.24, text: "大家不用再抢同一块蛋糕", en: "No more fighting over the same pie." },
  { from: 133.24, to: 134.12, text: "真到那天", en: "When that day comes," },
  { from: 134.12, to: 135.52, text: "经济规则要重写", en: "the rules of economics get rewritten," },
  { from: 135.52, to: 136.6, text: "连什么叫过得好", en: "even what a good life means" },
  { from: 136.6, to: 137.38, text: "人活着图什么", en: "and what we live for" },
  { from: 137.38, to: 138.42, text: "都得重新想了", en: "all need rethinking." },
  { from: 138.42, to: 141.08, text: "连这个亲手造 AI 的人 都在提醒你", en: "Even the man building AI is warning you:" },
  { from: 141.08, to: 142.9, text: "差距不会等到 2030 年", en: "the gap won't wait until 2030." },
  { from: 142.9, to: 144.88, text: "从今天谁在用 谁还在等", en: "From today, who's using it, who's waiting —" },
  { from: 144.88, to: 146.68, text: "就已经开始拉开差距了", en: "the gap is already opening up." },
  { from: 146.68, to: 148.12, text: "听完这些 你有什么想法呢", en: "What do you think?" },
  { from: 148.12, to: 149.1, text: "评论区告诉我", en: "Tell me in the comments." },
];
