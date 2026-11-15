# Hypit 视频拆解操作参考

本参考用于 `bela-wechat-video-download-copy-to-lark` 的分析子流程。它不替代上层下载、飞书和完整依赖门禁。工作目录、源文件、输出目录、工具路径和模型路径全部来自本次任务配置；不要写入作者电脑路径、个人链接或凭据。

## 1. 严格依赖门禁

**先检查全部依赖，再开始下载、识别、分析和归档。任何必需项缺失、不可读、版本不兼容或服务未就绪，都停止整个流程。** 列出缺失项、检查结果与用户需要完成的准备；用户安装或配置后，重新检查全部门禁，通过才继续。

仅已安装依赖 skill 的最新版本升级按主技能授权自动进行，升级后复检。禁止自动安装缺失 skill、CLI、Python 环境、包或模型；禁止自动运行 `npm install`、`npx` 安装、`brew install`、`pip install`、`hypit programs prepare/up`、`hypit runtime up`；禁止为了继续任务自动下载模型、切换识别后端、改用其他账号或退回只看字幕的分析。执行中发现依赖问题或所选后端失败，同样停止，不循环重试计费请求。

共同必需项：

| 依赖 | 只读检查 | 通过条件 |
| --- | --- | --- |
| `hypit` skill | 读取用户已安装的 `SKILL.md` 和 `references/creation/reference-video.md` | 两者存在、可读；按当前安装版本的说明执行 |
| Hypit CLI | `hypit version`、`hypit media --help` | 使用已经定位的可执行文件；需要的选项存在 |
| FFmpeg / FFprobe | `ffmpeg -version`、`ffprobe -version` | 两者均可执行，且后续 Hypit 能找到同一环境中的程序 |
| 识别模式 | 读取 `transcription.mode` | 明确为 `whisper-local` 或 `hypit-transcribe`；未选择则停止并让用户配置 |

下面命令里的 `hypit`、`whisper` 表示门禁已验证的真实可执行文件。项目内 CLI 可以使用已存在的本地 launcher；不要通过包管理器临时下载安装。记录版本和本次选择，但不要记录秘密值。

### 主模式：`whisper-local`

沿用本流程验证过的 standalone OpenAI Whisper 本地识别方式；**这不是 Hypit WhisperX**。

还必须满足：

- `whisper` CLI 已安装，`whisper --help` 成功，提供 `--model`、`--language`、`--device`、`--fp16` 和 `--word_timestamps`。
- 模型文件已在本机下载好。默认按 `transcription.model`（如 `small`）在 Whisper 缓存目录 `${XDG_CACHE_HOME:-~/.cache}/whisper/<model>.pt` 中查找；放在别处时才用 `transcription.model_path` 或环境变量 `WHISPER_MODEL_PATH` 显式指定。以 `check_dependencies.py` 输出中 `transcription.model_file.path` 的解析结果为准，检查为普通文件、可读、非空；可用用户提供或发布方明确提供的校验值核验完整性。
- 使用已有 CPU 环境；不因识别较慢切换模型、设备或服务。Apple Silicon/MPS 可用不等于所选识别器完整支持该后端。
- 文件缺失或损坏时停止；调用时 `--model` 只传解析出的绝对文件路径，不得直接传 `small`、`turbo` 等模型名称。这些名称可能触发下载。

只有安装成功不足以证明模型已准备；只有模型文件存在不足以证明推理会成功。首次实际执行若失败，保留错误并停止，由用户修复后复检。

### 可选模式：`hypit-transcribe`

仅当用户明确选择此模式并完成配置时使用，不能作为 `whisper-local` 的失败回退。

- `hypit paths` 显示明确选择的 Runtime Profile。
- Profile 中的 WhisperX alignment endpoint、绑定、语言和账号与用户选择一致。
- 本地 endpoint 已准备所选语音模型、该语言的 alignment 资源，并且服务已经运行；使用 `hypit programs status --endpoint <所选实例>` 和适用的 `hypit doctor --endpoint <所选实例>` 做只读核验。
- 托管 endpoint 的连接、能力和就绪检查通过；用户已经接受本次识别的计费账号、范围和预算。仅凭已登录不能视为付费授权。
- 不启动、准备、安装或更换 endpoint。不确定就绪情况时停止，说明需要用户完成的准备。

## 2. 固定所选模式后执行识别

先用源视频 probe 读取实际时长和流信息。保留下载原文件，分析副本、转录和网格写入独立工作目录。不要转码覆盖原文件。

主模式示例（`$WHISPER_CLI` 与 `$MODEL_FILE` 取自本次 `check_dependencies.py` 输出的 `transcription.whisper_cli.path` 和 `transcription.model_file.path`；所有路径必须引用）：

```sh
"$WHISPER_CLI" "$SOURCE_VIDEO" \
  --model "$MODEL_FILE" \
  --language zh --device cpu --fp16 False \
  --word_timestamps True --threads 4 \
  --output_format all --output_dir "$TRANSCRIPT_DIR"
```

`--language` 使用实际主语言，不能仅因说明是中文而固定选 `zh`。模型路径必须再次确认为本地现存文件。保留 Whisper 原始 JSON/SRT；`all` 还会输出 TXT/VTT/TSV。线程数可以由用户配置，不能改变所选模型或后端。

明确选择 `hypit-transcribe` 时：

```sh
hypit transcribe "$SOURCE_VIDEO" --language zh \
  --runtime "$HYPIT_RUNTIME_PROFILE" --to "$TRANSCRIPT_JSON"
```

这一步可能使用所选托管服务并产生费用。依赖门禁和对应付费范围未通过时不得执行。不要同时执行两个模式。

## 3. Whisper → Hypit 网格转录格式

已核验 Hypit 0.3.1 的网格解析器使用 `hypit.transcript@1`。新版本以当前 skill 和已安装 CLI 为准；接口不兼容时停止并报告；依赖 skill 依据上游更新，CLI 升级仍需用户完成，不能偷偷替换运行环境。

standalone Whisper 的原始 `segments` 需转换为 `passages`：

| Whisper JSON | Hypit JSON |
| --- | --- |
| 根对象 | 增加 `format: "hypit.transcript@1"` |
| `segments[]` | `passages[]` |
| `segments[].text` | `passages[].text` |
| `segments[].start` / `.end` | `passages[].start_seconds` / `.end_seconds` |
| `segments[].words[]` | `passages[].words[]` |
| `words[].word` | `words[].text` |
| `words[].start` / `.end` | `words[].start_seconds` / `.end_seconds` |
| `words[].probability`（如有） | `words[].score`（如有） |

示例结构（时间仅示意）：

```json
{
  "format": "hypit.transcript@1",
  "source": "source.mp4",
  "language": "zh",
  "audio_seconds": 12.3,
  "provenance": {
    "recognizer": "standalone OpenAI Whisper",
    "alignment": "Whisper word_timestamps; not WhisperX",
    "wording": "raw automatic recognition"
  },
  "passages": [
    {
      "text": "示例文本",
      "start_seconds": 0.2,
      "end_seconds": 1.5,
      "words": [
        {"text": "示例", "start_seconds": 0.2, "end_seconds": 0.8},
        {"text": "文本", "start_seconds": 0.8, "end_seconds": 1.5}
      ]
    }
  ]
}
```

- 时长来自 probe，不能硬编码。全部时间为**同一输入视频**的秒数；不要混用裁剪前后的时钟。
- 每个 word 的文本为字符串；存在的起止时间必须是有限、非负数字，结束不早于开始。不要把没有测得的时刻补为零。
- 只转换表示，不重新编造词级时间。若未生成词级结果，停止该分析步骤并说明原因，不能把整句话的时间复制到每个字冒充对齐。
- 原始 JSON 不修改。将对照烧录字幕或听辨得到的错词修正另存，并记录依据；引用文本不能把自动识别当作已核验原话。
- `hypit-transcribe` 已输出兼容格式时不再套用 Whisper 转换。

## 4. 已核验的 Hypit 媒体命令

以下语法由 Hypit 0.3.1 CLI 帮助与实际媒体操作核验。`media` 命令本地执行，不需要 Runtime Profile 或付费账户。示例区间按待分析视频调整，结束时间不得超出实际时长。

```sh
# 尺寸、帧率、时长、音视频流
hypit media probe "$SOURCE_VIDEO" --json

# 分页查看全片；转录词语显示在画面之外
hypit media tiles "$SOURCE_VIDEO" --every 1 \
  --columns 4 --rows 3 --cell 480 \
  --transcript "$TRANSCRIPT_JSON" --to "$OVERVIEW_DIR"

# 逐段近看：此处为 6.8–8.4 秒的示例区间
hypit media tile "$SOURCE_VIDEO" --start 6.8 --end 8.4 --every 0.1 \
  --columns 4 --cell 480 --transcript "$TRANSCRIPT_JSON" \
  --to "$DETAIL_GRID"

# 对短暂切换、弹入或遮挡逐帧检查
hypit media tiles "$SOURCE_VIDEO" --start 6.8 --end 8.4 --every-frame \
  --columns 4 --rows 3 --cell 480 --transcript "$TRANSCRIPT_JSON" \
  --to "$FRAME_GRID_DIR"

# 机械画面变化候选，结果不是剪辑镜头标签
hypit media boundaries "$SOURCE_VIDEO" --rate 4 --threshold 0.2 --json
```

`tile` 生成单张网格；`tiles` 分页。`--every` 从起点采样且不含终点，必要时另查最后一帧。`--every-frame` 保留选区每个原始帧。输出已存在时 CLI 会拒绝覆盖，应使用新证据文件名，不能删除旧证据来掩盖重复操作。

## 5. 分析与交付质量

先覆盖开头到结尾，再对转折、信息密集处和短暂动画加密检查。稀疏网格只能证明采样时刻的状态，不能证明间隔内没有变化。`boundaries` 的分数只是查找线索，不能自动等同“切镜头”。

拆解结论至少覆盖：

1. 视频想让观众知道、感受或采取什么行动；开场钩子、论证或故事、反转、兑现和结尾 CTA。
2. 带时间码的段落：口播/动作、画面内容、字幕/关键词/卡片/转场等如何同步，它们为什么有助于理解或停留。
3. 主要视觉系统：位置、层级、颜色、出现、变化、持续和退出；重复系统说明一次，并标出各次变化和例外。
4. 可复用的方法及适用边界，明确区分“直接观察”“原视频声称”和“分析判断”。不能凭一个视频推断真实完播率、商业效果或制作工具内部实现。
5. 证据与限制：使用的识别模式、人工核验范围、时间码精度、尚未确定的细节。

保留 `ANALYSIS.md`（整体理解）和 `TIMELINE.md`（具体时间与行为）作为工作记录。归档的拆解文档应可独立阅读，并链接原视频节点；内部网格、临时脚本、原始 ASR JSON/SRT 不自动作为额外云端文件上传；对外的原话以校对后的口播稿 `.md` 交付（见 report-spec 的「口播稿」）。

### 声音证据限制

ASR 可帮助确认口播文字和粗略时间；它不能证明背景音乐、音效种类、响度、声像、混音或表演语气。画面写着“音效”不等于听到了特定音效。

有实际音频听辨能力时，播放并检查完整音画及关键片段。没有音频听辨能力时，报告必须明确写明“基于视频画面与自动语音识别；背景音乐、音效及混音未逐项听辨”，删去没有证据的声音判断，不能声称已经完整听看。若任务要求完整声音拆解，则停止并说明该必要能力缺失，不能以字幕分析冒充完成。

技术失败或必需依赖缺失与证据范围限制不同：前者触发严格停止；后者只有在用户所需分析范围允许时才能带明确限制交付。不得把门禁失败重新描述成“限制”后继续归档。
