# Remotion 工程与已踩过的坑

## 环境

- 在复制出的工程目录执行 `npm install`（Remotion 4.0.484），同时准备 FFmpeg、Python 3 和 FontTools（提供 `pyftsubset`）。
- 参照 [案例时间轴数据](../examples/1102-哈萨比斯-data.ts) 新建 `src/data.ts`，填入本项目的片长、镜头、字幕和动效节点。可先复制案例查看类型和字段，案例引用的媒体不随包分发。
- 模板带[得意黑](https://github.com/atelier-anchor/smiley-sans)、[Noto Sans SC](https://github.com/google/fonts/tree/main/ofl/notosanssc)、[Orbitron](https://github.com/google/fonts/tree/main/ofl/orbitron) 和对应字体许可（见 `template/public/fonts/`）。英文字幕使用系统 Arial 或无衬线斜体。电子音效可使用 `python3 sfx-src/make_sfx.py public/sfx` 重新生成，需要 NumPy。
- 本人口播：`public/aroll-k.mp4`（由 `粗剪.mp4` 转 `-g 15`）；素材在 `public/v/`。
- 渲染：`./render.sh ../精剪初版.mp4`。每 900 帧一段（各自新开浏览器），画面无损拼接，声音整条单独渲染再合成。

## 坑与解法

| 现象 | 原因 | 解法 |
|---|---|---|
| `delayRender() "fonts" was called but not cleared`，约 60 秒后失败 | 在模块顶层调 delayRender 等字体，Remotion 额外开的页面里永远不清 | **把 delayRender 放进 Main 组件**（useState + useEffect），模块顶层只发起加载 |
| 字体加载慢 | 思源黑体 17 MB | 改字后先跑 `python3 make_font_subset.py` 生成子集；字幕得意黑用全量 |
| 长段渲染中途 `Request closed`、页面重载 | OffthreadVideo 帧缓存涨到 2 GB+ | 用 `@remotion/media` 的 `Video`；渲染加 `--offthreadvideo-cache-size-in-bytes=536870912`；分段渲染 |
| 跳点多的素材渲染极慢/卡死 | 素材关键帧间隔 7 秒以上 | 入工程前统一转 `-g 10` |
| 自制段落动画不动 | 组件里写死了旧的起始秒数 | 自制段落的起止时间放 data.ts（如 `SPEED`），组件用 `shot.from + frame/fps` |
| 另一个会话也在渲染 | 抢 CPU/内存 | `ps` 看一下；不动别人的进程，等它结束或降并发 |
| 只改字幕/一段画面 | 整片重渲 15 分钟 | 只渲受影响的 900 帧段，ffmpeg trim+concat 拼回，音频直接 copy |

## 检查脚本

- 节奏：`python3 "<本 Skill 目录>/scripts/check_rhythm.py" src/data.ts` 列出超过 3 秒没有任何变化点的区间。
- 抽帧：`ffmpeg -i 精剪初版.mp4 -vf "fps=1/2,scale=150:-1,tile=15x5" -frames:v 1 sheet.jpg`。
