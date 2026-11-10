---
name: bela-app-icon-picker
description: >
  获取、下载、提取并处理高质量 App 图标：优先从本机 .app 或 App Store
  获取官方图标，核对 bundleId，输出 1024px、透明背景、iOS 圆角 PNG。
  用户只要表达“要某个应用的图标”就使用本 Skill，包括极短指令和应用名列表，
  例如“新的图标 WorkBuddy、Codex”“补两个图标”“WorkBuddy 和 Codex 图标”
  “下载图标”“找图标”“应用图标”“App logo”“提取/抠出软件图标”，以及为
  设计素材、PPT、封面、文章或图标库收集 App 图片。英文请求如 get/download/
  extract/collect app icon or app logo 也应触发。
---

# Bela App Icon Picker

Download official high-quality app icons and process them into clean transparent PNGs with iOS-style rounded corners.

## Overview

This skill handles the full pipeline:
1. **Search** — Find the app on the App Store via iTunes Search API
2. **Download** — Get the highest resolution icon available (1024px)
3. **Process** — Apply iOS rounded corners with clean transparency (no white fringe)
4. **Save** — Output as PNG to the user's specified folder

## Execution environment

Run search, extraction, download, and image processing on the user's Mac with the
available local terminal/process tool. Do not require a specific legacy tool name.
Use `python3` with Pillow (PIL).

If Pillow is not installed, run: `pip3 install Pillow`

## Default output folder

Save icons to the requested folder. When the user has no preference, use `./app-icons/` in the current workspace.

## Step 1: Search App Store

Use the iTunes Search API to find apps. The key is matching the correct app by `bundleId`.

```python
import urllib.request, json

term = "AppName"
country = "us"  # "us" for international apps, "cn" for China-only apps
url = f"https://itunes.apple.com/search?term={term.replace(' ', '+')}&country={country}&entity=software&limit=10"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
data = json.loads(urllib.request.urlopen(req).read())
for r in data["results"]:
    print(f"{r['trackName']} | {r['bundleId']} | {r['artworkUrl512']}")
```

### Bundle ID verification

Always verify by `bundleId` to avoid downloading the wrong icon. Known bundle IDs:

| App | bundleId | Store |
|-----|----------|-------|
| 豆包 | com.bot.doubao | cn |
| ChatGPT | com.openai.chat | us |
| Claude | com.anthropic.claude | us |
| NotebookLM | com.google.NotebookLM | us |
| 千问 (通义千问) | com.aliyun.ios.tongyi | cn |
| Kimi | com.moonshot.kimichat | us |
| Telegram | ph.telegra.Telegraph | us |
| Manus | tech.butterfly.app | us |
| YouTube | com.google.ios.youtube | us |
| Instagram | com.burbn.instagram | us |
| Netflix | com.netflix.Netflix | us |
| DeepSeek | com.deepseek.chat | us |
| 即梦 | com.bytedance.dreamina | cn |
| 海螺 | com.hailuoai.video | cn |
| MiniMax | com.ai.wanjuan | cn |
| Gemini | com.google.gemini | us |
| Figma | com.figma.FigmaMirror | us |
| Grok | ai.x.GrokApp | us |
| WorkBuddy | com.workbuddy.workbuddy | local macOS app |
| Codex | com.openai.codex | local macOS app, currently hosted by ChatGPT.app |

If a search returns wrong results, try:
- Searching the US store instead of CN (or vice versa)
- Using the app's English name
- Adding the company name to the search term

### Desktop-only apps (no App Store listing)

Some apps like Cursor, VS Code are desktop-only. For these:
1. Check if installed: `mdfind 'kMDItemFSName == "AppName.app"'`
2. Read `Contents/Info.plist` and verify `CFBundleIdentifier`.
3. Find the actual icon resource under `Contents/Resources`; do not assume its filename matches the app.
4. Extract icon: `sips -s format png /path/to/icon.icns --out /tmp/icon.png`
5. For Codex on this Mac, check `/Applications/ChatGPT.app/Contents/Resources/app.icns`.
6. For WorkBuddy on this Mac, check `/Applications/WorkBuddy.app/Contents/Resources/icon.icns`.
7. Resize to 1024px during processing.

## Step 2: Download 1024px Icon

Convert the App Store artwork URL from 512px to 1024px:

```python
icon_url = artwork_url.replace("/512x512bb.jpg", "/1024x1024bb.png")
```

## Step 3: Process with Rounded Corners

Use `scripts/process_icon.py` (bundled with this skill). Core function:

```python
from process_icon import make_clean_rounded_icon, download_appstore_icon, extract_local_app_icon

# From App Store
img = download_appstore_icon("ChatGPT", country="us", bundle_id="com.openai.chat")
result = make_clean_rounded_icon(img, target_size=1024)
result.save("ChatGPT.png")

# From local .app
img = extract_local_app_icon("Cursor")
result = make_clean_rounded_icon(img, target_size=1024)
result.save("Cursor.png")
```

Processing details:
- 4x supersampled anti-aliased rounded corner mask (iOS standard: 22.37% radius)
- Mask erosion to eliminate fringe pixels
- Semi-transparent edge pixel RGB cleanup (replaces white with nearest opaque neighbor)
- Fully transparent pixels set to RGBA(0,0,0,0)

## Step 4: Batch Processing

For multiple icons, combine in a single script to minimize round-trips:

```python
apps = {
    "ChatGPT": ("ChatGPT", "us", "com.openai.chat"),
    "Claude":  ("Claude",  "us", "com.anthropic.claude"),
}
for name, (term, country, bundle_id) in apps.items():
    img = download_appstore_icon(term, country, bundle_id)
    if img:
        result = make_clean_rounded_icon(img)
        result.save(f"./app-icons/{name}.png")
```

## Common Issues

**Wrong app returned**: Filter by `bundleId`. Try different search terms or country store.

**White fringe in photo editors**: The processing script fixes this. If it still appears, use `--no-antialias` for a fully binary mask.

**Low resolution from .icns**: macOS `.icns` max at 512px. Resize to 1024px with `Image.LANCZOS`.
