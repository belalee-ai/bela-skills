#!/usr/bin/env python3
"""
App Icon Processor - iOS-style rounded corners with clean transparency.

Usage:
    python3 process_icon.py input.png output.png [--size 1024] [--no-antialias]

Or import:
    from process_icon import make_clean_rounded_icon, download_appstore_icon
"""

import argparse
from PIL import Image, ImageChops, ImageDraw


def make_clean_rounded_icon(img, target_size=1024, antialias=True):
    """Apply iOS-style rounded corners with clean transparent edges."""
    img = img.convert('RGBA')
    if img.size[0] != target_size or img.size[1] != target_size:
        img = img.resize((target_size, target_size), Image.LANCZOS)
    size = target_size
    radius = int(size * 0.2237)

    if antialias:
        scale = 4
        big_size = size * scale
        big_radius = radius * scale
        mask_big = Image.new('L', (big_size, big_size), 0)
        draw = ImageDraw.Draw(mask_big)
        draw.rounded_rectangle([0, 0, big_size - 1, big_size - 1], radius=big_radius, fill=255)
        mask = mask_big.resize((size, size), Image.LANCZOS)
        mask = mask.point(lambda x: max(0, min(255, int((x - 8) * 255 / (255 - 8)))) if x > 8 else 0)
    else:
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    # Preserve transparency already present in local .app icons. Multiplying the
    # source alpha by the rounded mask avoids turning transparent source pixels
    # into black wedges around an icon that already has rounded corners.
    source_alpha = img.getchannel('A')
    final_alpha = ImageChops.multiply(source_alpha, mask)
    result = img.copy()
    result.putalpha(final_alpha)

    if antialias:
        pixels = result.load()
        for y in range(size):
            for x in range(size):
                a = pixels[x, y][3]
                if 0 < a < 240:
                    found = False
                    for dy in range(-3, 4):
                        for dx in range(-3, 4):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < size and 0 <= ny < size:
                                if pixels[nx, ny][3] >= 240:
                                    best_r, best_g, best_b = pixels[nx, ny][:3]
                                    found = True
                                    break
                        if found:
                            break
                    if found:
                        pixels[x, y] = (best_r, best_g, best_b, a)
                elif a == 0:
                    pixels[x, y] = (0, 0, 0, 0)
    return result


def download_appstore_icon(app_name, country="us", bundle_id=None):
    """Search iTunes API and download the 1024px icon. Returns PIL Image or None."""
    import urllib.request, json, io
    term = app_name.replace(" ", "+")
    url = f"https://itunes.apple.com/search?term={term}&country={country}&entity=software&limit=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req).read())
    match = None
    for r in data["results"]:
        if bundle_id and r["bundleId"] == bundle_id:
            match = r
            break
    if not match and data["results"] and not bundle_id:
        match = data["results"][0]
    if not match:
        print(f"[WARN] No match for '{app_name}' (bundle_id={bundle_id})")
        return None
    icon_url = match["artworkUrl512"].replace("/512x512bb.jpg", "/1024x1024bb.png")
    print(f"  Found: {match['trackName']} ({match['bundleId']})")
    req = urllib.request.Request(icon_url, headers={"User-Agent": "Mozilla/5.0"})
    return Image.open(io.BytesIO(urllib.request.urlopen(req).read()))


def extract_local_app_icon(app_name):
    """Extract icon from a locally installed macOS .app bundle."""
    import subprocess, os
    result = subprocess.run(["mdfind", f'kMDItemFSName == "{app_name}.app"'], capture_output=True, text=True)
    app_path = result.stdout.strip().split("\n")[0] if result.stdout.strip() else None
    if not app_path:
        print(f"[WARN] {app_name}.app not found locally")
        return None
    resources = os.path.join(app_path, "Contents", "Resources")
    if not os.path.isdir(resources):
        return None
    icns_files = [f for f in os.listdir(resources) if f.endswith(".icns")]
    target_icns = None
    for f in icns_files:
        if app_name.lower() in f.lower():
            target_icns = os.path.join(resources, f)
            break
    if not target_icns and icns_files:
        target_icns = os.path.join(resources, icns_files[0])
    if not target_icns:
        return None
    tmp_png = f"/tmp/{app_name}_icon_extracted.png"
    subprocess.run(["sips", "-s", "format", "png", target_icns, "--out", tmp_png], capture_output=True)
    print(f"  Extracted from {target_icns}")
    return Image.open(tmp_png)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process app icon with iOS rounded corners")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--size", type=int, default=1024, help="Output size (default: 1024)")
    parser.add_argument("--no-antialias", action="store_true", help="Binary mask, no anti-aliasing")
    args = parser.parse_args()
    img = Image.open(args.input)
    result = make_clean_rounded_icon(img, target_size=args.size, antialias=not args.no_antialias)
    result.save(args.output)
    print(f"Saved: {args.output} ({result.size[0]}x{result.size[1]})")
