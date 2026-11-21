# Hypit 视频拆解操作参考

本参考用于解析已验证的本地源文件，按时间轴核对口播与画面。原片、转录、证据图和工作记录放在本条作品的工作区。

## 1. 选择识别方式

按[首次准备](setup-and-updates.md)安装缺少的普通依赖后复检。从检查结果取 Hypit、Whisper 和模型的实际路径，读取已安装 Hypit 的 `references/creation/reference-video.md`。从原片做媒体探测；无音轨或没有口播时写明这点，继续完成有证据的画面分析。

默认 `whisper-local` 使用 standalone OpenAI Whisper 和本地 CPU，输出自动识别及词级时间。优先复用已有 CLI、模型路径和配置。首次缺少命名模型时按选定名称下载并加载，再把实际缓存路径交给识别器。

已明确选用 `hypit-transcribe` 时，检查指定 Profile、语言及其 WhisperX alignment endpoint 是否一致。可用已定位的 Hypit CLI 运行 `hypit doctor --runtime "$HYPIT_RUNTIME_PROFILE" --endpoint "$HYPIT_ENDPOINT"` 检查这个 endpoint。仅在用户已选择并授权该托管服务、本次素材外传和相应费用时调用它。服务不可用时保留素材、报告原因，可继续整理已有画面证据。

## 2. 固定所选模式后执行识别

先用源视频 probe 读取实际时长和流信息。保留下载原文件，分析副本、转录和网格写入独立工作目录。不要转码覆盖原文件。

主模式示例（ASR_LANGUAGE 与 ASR_THREADS 来自配置，`$WHISPER_CLI` 与 `$MODEL_FILE` 取自本次 `check_dependencies.py` 输出的 `transcription.whisper_cli.path` 和 `transcription.model_file.path`；所有路径必须引用）：

```sh
"$WHISPER_CLI" "$SOURCE_VIDEO" \
  --model "$MODEL_FILE" \
  --language "$ASR_LANGUAGE" --device cpu --fp16 False \
  --word_timestamps True --threads "$ASR_THREADS" \
  --output_format all --output_dir "$TRANSCRIPT_DIR"
```

`--language` 使用实际主语言，不能仅因说明是中文而固定选 `zh`。模型路径必须再次确认为本地现存文件。保留 Whisper 原始 JSON/SRT；`all` 还会输出 TXT/VTT/TSV。线程数可以由用户配置，不能改变所选模型或后端。

明确选择 `hypit-transcribe` 时：

```sh
hypit transcribe "$SOURCE_VIDEO" --language "$ASR_LANGUAGE" \
  --runtime "$HYPIT_RUNTIME_PROFILE" --to "$TRANSCRIPT_JSON"
```

这一步可能使用所选托管服务并产生费用。按已选 Profile 核实对应服务与费用范围。一次识别使用一种模式。

## 3. Whisper → Hypit 网格转录格式

已核验 Hypit 0.3.1 的网格解析器使用 `hypit.transcript@1`。新版本以当前 Skill 和已安装 CLI 帮助为准；若所选版本缺能力，沿原安装渠道补齐后复检。

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
- 只转换表示，不重新编造词级时间。若未生成词级结果，保留已有段落时间，标注精度；逐词同步的结论留待核验。
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

可在工作区保留 `ANALYSIS.md`（整体理解）和 `TIMELINE.md`（逐段证据）。按[报告与口播稿要求](report-spec.md)交付两份独立文稿：拆解文档配上代表性的时间码证据图，口播稿保存校对后的原话。内部网格和原始 ASR JSON/SRT 用于核查。

### 声音证据限制

ASR 可帮助确认口播文字和粗略时间；它不能证明背景音乐、音效种类、响度、声像、混音或表演语气。画面写着“音效”不等于听到了特定音效。

有实际音频听辨能力时，播放并检查完整音画及关键片段。没有音频听辨能力时，报告必须明确写明“基于视频画面与自动语音识别；背景音乐、音效及混音未逐项听辨”，删去没有证据的声音判断，不能声称已经完整听看。若任务要求完整声音拆解，则停止并说明该必要能力缺失，不能以字幕分析冒充完成。

记录技术失败影响的具体产物。依赖或服务恢复后复用原片、转录和已核验的画面证据继续。
