# 素材来源

## 优先级

1. **参考视频里的视频素材**：只复用有权使用的片段，保留素材授权要求的署名或标记。先判断是不是真视频：画面整段不动或只有缓慢推拉的 AI 生成图，按静帧处理，不用。
2. **真人真实画面**：提到的人物一定要有本人视频。YouTube 搜「人名 + 场合」（如 `Demis Hassabis Stanford`），优先官方频道、演讲、采访、纪录片。
3. **Mixkit 高清实拍**（免费，可直接下载）：医生、理财、学习、手机、工厂、火、山、城市、人群、钱、机器人、数据中心等日常画面。
4. **自制动效**：数据对比、数字、两条线这类信息图；做在实拍底上或深色底上，不能只做文字卡。

Pexels 会拦截命令行请求，不用。

## YouTube（yt-dlp）

```bash
yt-dlp "ytsearch6:关键词" --flat-playlist --print "%(id)s | %(duration_string)s | %(channel)s | %(title)s"
# 先下 360p 全片扫时间点
yt-dlp -f "bv*[height<=360][ext=mp4]" -o "%(id)s.%(ext)s" URL
# 再只下需要的 10 秒 1080p
yt-dlp -f "bv*[height<=1080][ext=mp4]" --download-sections "*起-止" --force-keyframes-at-cuts -o "{id}_{起}.%(ext)s" URL
```

- 报 403：先 `brew upgrade yt-dlp`。个别片段要求登录验证就换同视频别的时间点，不绕验证。
- 扫全片：`fps=1/30` 带时间码拼成联系表。**联系表时间和下载片段对不上是常事**，下载后必须对每个片段在拟用入点重新截图确认画面。
- 片段内部切镜：`select='gt(scene,0.3)',showinfo` 列出切点，入点和时长避开切点。

## Mixkit

页面 `https://mixkit.co/free-stock-video/<主题>/`，视频直链 `https://assets.mixkit.co/videos/<id>/<id>-1080.mp4`（没有就 `-720.mp4`）。用 alt 文本和最近的视频 id 对应标题；下载后截第 2 秒拼联系表确认内容。

## 入工程前统一格式

```bash
ffmpeg -i in.mp4 -an -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30" \
  -c:v libx264 -crf 20 -preset veryfast -g 10 -pix_fmt yuv420p public/v/<名>.mp4
```

`-g 10` 很关键：关键帧稀疏的素材在 Remotion 里频繁跳点会卡死渲染。

## 记录

所有来源写进 `素材/来源.md`：文件前缀、原视频标题/频道或 Mixkit 编号、用途。记录许可或授权依据和署名要求。
