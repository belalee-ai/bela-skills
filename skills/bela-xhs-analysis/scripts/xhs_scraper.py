#!/usr/bin/env python3
"""
小红书竞品笔记抓取工具
用法：python3 scripts/xhs_scraper.py <用户主页URL>

首次使用需要配置 cookie：
1. 打开 Chrome，登录小红书 www.xiaohongshu.com
2. F12 → Application → Cookies → 复制 web_session 的值
3. 设置环境变量：export XHS_COOKIE="web_session=你的值"
   或创建 .env 文件：echo 'XHS_COOKIE=web_session=xxx' > scripts/.env

脚本会自动：
- 抓取用户所有笔记标题、互动数据
- 抓取每篇笔记的详细文案（desc）
- 输出为 markdown 格式的竞品分析文档
"""

import sys
import re
import json
import time
import os
import urllib.request
import urllib.parse

def get_cookie():
    """从环境变量或 .env 文件获取 cookie"""
    cookie = os.environ.get('XHS_COOKIE', '')
    if not cookie:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith('XHS_COOKIE='):
                        cookie = line.strip().split('=', 1)[1]
    return cookie

def fetch_page(url, cookie=''):
    """Fetch a page with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    if cookie:
        headers['Cookie'] = cookie

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode('utf-8')

def extract_ssr_data(html):
    """Extract __INITIAL_STATE__ from page HTML"""
    match = re.search(r'window\.__INITIAL_STATE__=({.*?})\s*</script>', html, re.DOTALL)
    if not match:
        start = html.index('window.__INITIAL_STATE__=') + len('window.__INITIAL_STATE__=')
        end = html.index('</script>', start)
        raw = html[start:end]
    else:
        raw = match.group(1)

    raw = raw.replace(':undefined', ':null').replace(',undefined', ',null')
    return json.loads(raw)

def get_profile_notes(user_url):
    """从用户主页提取所有笔记的基本信息"""
    html = fetch_page(user_url)
    data = extract_ssr_data(html)

    # Extract user info
    user_data = data.get('user', {}).get('userPageData', {})
    basic = user_data.get('basicInfo', {})

    # v0.3.0+ S2: 加 fans / userId / 关注 / 总赞
    interactions = user_data.get('interactions', [])
    fans, total_likes, follows = '', '', ''
    for inter in interactions:
        t = inter.get('type', '')
        v = inter.get('count', '')
        if t == 'fans':
            fans = v
        elif t == 'interaction':
            total_likes = v
        elif t == 'follows':
            follows = v

    user_info = {
        'nickname': basic.get('nickname', ''),
        'desc': basic.get('desc', ''),
        'ip': basic.get('ipLocation', ''),
        'redId': basic.get('redId', ''),
        # v0.3.0+ S2: 新增字段（向后兼容，旧调用者无感）
        'fans': fans,
        'total_likes': total_likes,
        'follows': follows,
        'userId': basic.get('redOfficialVerifyType', ''),  # may be empty; userId 从 URL 解析更稳
        'imageb': basic.get('imageb', ''),
    }

    # Extract notes
    notes_raw = data.get('user', {}).get('notes', [])
    if notes_raw and isinstance(notes_raw[0], list):
        notes_raw = notes_raw[0]

    notes = []
    for note in notes_raw:
        card = note.get('noteCard', {})
        interact = card.get('interactInfo', {})
        # v0.3.0+ S2: 加 collects / comments / time / cornerTag
        notes.append({
            'title': card.get('displayTitle', ''),
            'type': card.get('type', ''),
            'likes': interact.get('likedCount', ''),
            'sticky': interact.get('sticky', False),
            'xsecToken': card.get('xsecToken', ''),
            'noteId': card.get('noteId', note.get('id', '')),
            # S2 新增
            'collects': interact.get('collectedCount', ''),
            'comments': interact.get('commentCount', ''),
            'shares': interact.get('shareCount', ''),
            'cornerTag': (card.get('cornerTagInfo', [{}]) or [{}])[0].get('text', '') if card.get('cornerTagInfo') else '',
            'cover': (card.get('cover', {}) or {}).get('urlDefault', ''),
        })

    return user_info, notes

def extract_comments_from_ssr(data):
    """从 SSR 数据中提取评论内容（首批评论已包含在页面中）"""
    comments = []
    try:
        # 尝试多种可能的 SSR 数据结构
        comment_data = data.get('comment', {}) or data.get('note', {}).get('comment', {})
        comment_list = (
            comment_data.get('comments', [])
            or comment_data.get('commentList', [])
            or comment_data.get('list', [])
        )

        for c in comment_list:
            content = c.get('content', '') or c.get('text', '')
            if not content:
                continue
            user_info = c.get('userInfo', {}) or c.get('user', {})
            comment_entry = {
                'content': content,
                'likes': c.get('likeCount', 0) or c.get('likes', 0),
                'nickname': user_info.get('nickname', ''),
            }
            comments.append(comment_entry)

            # 提取子回复（如果有）
            sub_comments = c.get('subComments', []) or c.get('replies', [])
            for sc in sub_comments:
                sub_content = sc.get('content', '') or sc.get('text', '')
                if sub_content:
                    sub_user = sc.get('userInfo', {}) or sc.get('user', {})
                    comments.append({
                        'content': sub_content,
                        'likes': sc.get('likeCount', 0) or sc.get('likes', 0),
                        'nickname': sub_user.get('nickname', ''),
                    })
    except Exception:
        pass
    return comments


def get_note_detail(note_id, cookie, xsec_token='', fetch_comments=False):
    """抓取单篇笔记的详细内容（需要 cookie）

    Args:
        fetch_comments: 是否同时提取评论（仅对高互动笔记开启）
    """
    if not note_id or not cookie:
        return None

    url = f'https://www.xiaohongshu.com/explore/{note_id}'
    if xsec_token:
        url += f'?xsec_token={urllib.parse.quote(xsec_token)}'

    try:
        html = fetch_page(url, cookie)
        data = extract_ssr_data(html)

        note_map = data.get('note', {}).get('noteDetailMap', {})
        for nid, detail in note_map.items():
            note = detail.get('note', {})
            if note:
                interact = note.get('interactInfo', {})
                # v0.3.0+ S2: 提取作者信息（在 note.user 或 note.userInfo 下）
                user = note.get('user') or note.get('userInfo') or {}
                result = {
                    'title': note.get('title', ''),
                    'desc': note.get('desc', ''),
                    'type': note.get('type', ''),
                    'likes': interact.get('likedCount', ''),
                    'comments': interact.get('commentCount', ''),
                    'collects': interact.get('collectedCount', ''),
                    'shares': interact.get('shareCount', ''),
                    'tags': [t.get('name', '') for t in note.get('tagList', [])],
                    # v0.3.0+ S2: 发布时间 + IP
                    'time': note.get('time', ''),
                    'lastUpdateTime': note.get('lastUpdateTime', ''),
                    'ip': note.get('ipLocation', ''),
                    'comments_disabled': not interact.get('commentEntries', True),
                    # v0.3.0+ S2: 作者信息
                    'author_userId': user.get('userId', '') or user.get('id', ''),
                    'author_nickname': user.get('nickname', '') or user.get('name', ''),
                    'author_avatar': user.get('avatar', ''),
                    'author_xsec_token': user.get('xsecToken', ''),
                }
                # 高互动笔记：从 SSR 数据中提取评论
                if fetch_comments:
                    result['comment_list'] = extract_comments_from_ssr(data)
                return result
    except Exception as e:
        print(f"  Error fetching {note_id}: {e}", file=sys.stderr)

    return None

def generate_markdown(user_info, notes, details):
    """生成 Markdown 竞品分析报告"""
    lines = []
    lines.append(f"# 竞品案例：{user_info['nickname']}\n")
    lines.append(f"## 博主概况\n")
    lines.append(f"- **昵称**：{user_info['nickname']}")
    lines.append(f"- **红薯号**：{user_info['redId']}")
    lines.append(f"- **简介**：{user_info['desc']}")
    lines.append(f"- **IP属地**：{user_info['ip']}")
    lines.append(f"- **总笔记数**：{len(notes)}\n")

    lines.append(f"## 笔记列表\n")
    lines.append("| # | 标题 | 类型 | 点赞 | 收藏 | 评论 | 备注 |")
    lines.append("|---|------|------|------|------|------|------|")

    for i, note in enumerate(notes):
        title = note['title']
        ntype = '视频' if note['type'] == 'video' else '图文'
        likes = note['likes']
        detail = details.get(i, {})
        collects = detail.get('collects', '-')
        comments = detail.get('comments', '-')
        pin = ' 📌' if note.get('sticky') else ''
        lines.append(f"| {i+1} | {title} | {ntype} | {likes} | {collects} | {comments} | {pin} |")

    # Add detailed descriptions for video notes
    video_notes_with_desc = [(i, n, details.get(i, {})) for i, n in enumerate(notes)
                              if n['type'] == 'video' and details.get(i, {}).get('desc')]

    if video_notes_with_desc:
        lines.append(f"\n## 视频文案详情\n")
        for i, note, detail in video_notes_with_desc:
            lines.append(f"### {i+1}. {note['title']}\n")
            lines.append(f"**点赞**: {detail.get('likes', '-')} | **收藏**: {detail.get('collects', '-')} | **评论**: {detail.get('comments', '-')}")
            if detail.get('tags'):
                lines.append(f"**标签**: {', '.join(detail['tags'])}\n")
            lines.append(f"**文案**：\n")
            lines.append(f"> {detail['desc']}\n")

    # 用户评论汇总（仅展示有评论数据的笔记）
    notes_with_comments = [(i, n, details.get(i, {})) for i, n in enumerate(notes)
                            if details.get(i, {}).get('comment_list')]

    if notes_with_comments:
        lines.append(f"\n## 用户评论摘要（高互动笔记）\n")
        for i, note, detail in notes_with_comments:
            comment_list = detail['comment_list']
            lines.append(f"### {i+1}. {note['title']}\n")
            lines.append(f"共获取 {len(comment_list)} 条评论：\n")
            # 按点赞数排序，优先展示高赞评论
            sorted_comments = sorted(comment_list,
                                      key=lambda c: c.get('likes', 0),
                                      reverse=True)
            for c in sorted_comments[:20]:  # 每篇最多展示 20 条
                likes_str = f" (👍{c['likes']})" if c.get('likes') else ''
                lines.append(f"- {c['content']}{likes_str}")
            if len(sorted_comments) > 20:
                lines.append(f"- *...还有 {len(sorted_comments) - 20} 条评论*")
            lines.append('')

    lines.append(f"\n---\n*抓取时间：{time.strftime('%Y-%m-%d %H:%M')}*")
    return '\n'.join(lines)

def verify_cookie(cookie, user_url):
    """验证 cookie 是否有效。返回 True/False"""
    if not cookie:
        return False
    try:
        html = fetch_page(user_url, cookie)
        data = extract_ssr_data(html)
        notes_raw = data.get('user', {}).get('notes', [])
        if notes_raw and isinstance(notes_raw[0], list):
            notes_raw = notes_raw[0]
        if notes_raw:
            first_id = notes_raw[0].get('noteCard', {}).get('noteId', '')
            return bool(first_id)
    except Exception:
        pass
    return False


def parse_note_id_from_url(url):
    """从笔记 URL 中提取 noteId"""
    # /explore/{noteId} 或 /discovery/item/{noteId}
    match = re.search(r'(?:explore|discovery/item)/([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return None


def parse_xsec_token_from_url(url):
    """从 URL 中提取 xsec_token 参数"""
    match = re.search(r'xsec_token=([^&\s]+)', url)
    if match:
        return match.group(1)
    return ''


def fetch_single_note(note_url, cookie=''):
    """抓取单篇笔记的完整数据（含评论）"""
    note_id = parse_note_id_from_url(note_url)
    if not note_id:
        print(f"  Error: 无法从 URL 中提取 noteId: {note_url[:60]}", file=sys.stderr)
        return None

    xsec_token = parse_xsec_token_from_url(note_url)

    # 构造标准 explore URL
    url = f'https://www.xiaohongshu.com/explore/{note_id}'
    if xsec_token:
        url += f'?xsec_token={urllib.parse.quote(xsec_token)}'

    try:
        html = fetch_page(url, cookie)
        data = extract_ssr_data(html)

        note_map = data.get('note', {}).get('noteDetailMap', {})
        for nid, detail in note_map.items():
            note = detail.get('note', {})
            if note:
                interact = note.get('interactInfo', {})
                user = note.get('user', {})
                result = {
                    'noteId': nid,
                    'title': note.get('title', ''),
                    'desc': note.get('desc', ''),
                    'type': note.get('type', ''),
                    'likes': interact.get('likedCount', ''),
                    'comments': interact.get('commentCount', ''),
                    'collects': interact.get('collectedCount', ''),
                    'shares': interact.get('shareCount', ''),
                    'tags': [t.get('name', '') for t in note.get('tagList', [])],
                    'author': {
                        'nickname': user.get('nickname', ''),
                        'userId': user.get('userId', ''),
                    },
                    'comment_list': extract_comments_from_ssr(data),
                }
                return result
    except Exception as e:
        print(f"  Error fetching note {note_id}: {e}", file=sys.stderr)

    return None


def generate_note_markdown(notes_data):
    """为单篇/多篇笔记生成 Markdown 分析数据（原始数据，AI 负责深度分析）"""
    lines = []
    multi = len(notes_data) > 1

    if multi:
        lines.append(f"# 多篇笔记数据汇总（共 {len(notes_data)} 篇）\n")
    else:
        lines.append(f"# 笔记数据：{notes_data[0].get('title', '未知标题')}\n")

    for i, note in enumerate(notes_data):
        if multi:
            lines.append(f"---\n## 笔记 {i+1}：{note.get('title', '未知标题')}\n")
        lines.append(f"- **作者**：{note.get('author', {}).get('nickname', '未知')}")
        lines.append(f"- **userId**：{note.get('author', {}).get('userId', '')}")
        lines.append(f"- **类型**：{'视频' if note.get('type') == 'video' else '图文'}")
        lines.append(f"- **点赞**：{note.get('likes', '-')} | **收藏**：{note.get('collects', '-')} | **评论**：{note.get('comments', '-')} | **分享**：{note.get('shares', '-')}")
        if note.get('tags'):
            lines.append(f"- **标签**：{', '.join(note['tags'])}")
        lines.append('')

        if note.get('desc'):
            lines.append(f"### 完整文案\n")
            lines.append(f"> {note['desc']}\n")

        if note.get('comment_list'):
            comment_list = note['comment_list']
            # 数字化点赞数（兼容 "1万+"、"1.2万"、"5000+" 等字符串）以防 sort 报错
            def _likes_num(c):
                v = c.get('likes', 0)
                if isinstance(v, (int, float)): return int(v)
                s = str(v).strip().replace(',', '').replace('+', '')
                try:
                    if '万' in s: return int(float(s.replace('万', '')) * 10000)
                    if 'w' in s.lower(): return int(float(s.lower().replace('w', '')) * 10000)
                    return int(float(s))
                except (ValueError, TypeError): return 0
            sorted_comments = sorted(comment_list, key=_likes_num, reverse=True)

            # Top 5 高赞评论（独立段，供口播文案参考）
            top_n = min(5, len(sorted_comments))
            lines.append(f"### Top {top_n} 高赞评论\n")
            lines.append("| # | 👍 | 评论内容 | 用户 |")
            lines.append("|---|---|---------|------|")
            for i, c in enumerate(sorted_comments[:5], 1):
                content = (c.get('content', '') or '').replace('|', '\\|').replace('\n', ' ')
                nick = (c.get('nickname', '') or '匿名').replace('|', '\\|')
                lines.append(f"| {i} | {c.get('likes', 0)} | {content} | {nick} |")
            lines.append('')

            # 完整评论列表（最多 20 条，供分析用）
            lines.append(f"### 全部评论（共 {len(comment_list)} 条，显示前 20）\n")
            for c in sorted_comments[:20]:
                likes_str = f" (👍{c['likes']})" if c.get('likes') else ''
                lines.append(f"- {c['content']}{likes_str}")
            if len(sorted_comments) > 20:
                lines.append(f"- *...还有 {len(sorted_comments) - 20} 条评论*")
            lines.append('')

    lines.append(f"\n---\n*抓取时间：{time.strftime('%Y-%m-%d %H:%M')}*")
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    output_format = 'markdown'
    if '--json' in sys.argv:
        output_format = 'json'

    # 单篇/多篇笔记模式
    if '--note' in sys.argv:
        note_urls = [a for a in sys.argv[1:] if a not in ('--note', '--json')]
        if not note_urls:
            print("Error: --note 模式需要提供笔记链接", file=sys.stderr)
            sys.exit(1)

        cookie = get_cookie()
        notes_data = []
        for i, nurl in enumerate(note_urls):
            print(f"🔍 [{i+1}/{len(note_urls)}] 抓取笔记...", file=sys.stderr)
            result = fetch_single_note(nurl, cookie)
            if result:
                print(f"  ✅ {result['title'][:40]} | 👍{result['likes']} 💬{result['comments']}", file=sys.stderr)
                if result.get('comment_list'):
                    print(f"     → 获取 {len(result['comment_list'])} 条评论", file=sys.stderr)
                notes_data.append(result)
            else:
                print(f"  ❌ 抓取失败: {nurl[:60]}", file=sys.stderr)
            if i < len(note_urls) - 1:
                time.sleep(1)

        if not notes_data:
            print("Error: 未能成功抓取任何笔记", file=sys.stderr)
            sys.exit(1)

        if output_format == 'json':
            print(json.dumps(notes_data, ensure_ascii=False, indent=2))
        else:
            print(generate_note_markdown(notes_data))
        sys.exit(0)

    # cookie 验证模式
    url = sys.argv[1]
    if '--verify-cookie' in sys.argv:
        cookie = get_cookie()
        valid = verify_cookie(cookie, url)
        print(json.dumps({"valid": valid, "cookie_exists": bool(cookie)}))
        sys.exit(0 if valid else 1)

    match = re.search(r'profile/([a-f0-9]+)', url)
    if not match:
        print("Error: Invalid user profile URL (use --note for note URLs)", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 抓取用户主页...", file=sys.stderr)
    user_info, notes = get_profile_notes(url)
    print(f"✅ 找到 {len(notes)} 篇笔记 | 用户: {user_info['nickname']}", file=sys.stderr)

    cookie = get_cookie()
    details = {}
    top_n = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 10

    if cookie:
        print(f"🔐 检测到 cookie，开始抓取笔记详情...", file=sys.stderr)
        for i, note in enumerate(notes):
            if note['noteId']:
                print(f"  [{i+1}/{len(notes)}] {note['title'][:30]}...", file=sys.stderr)
                detail = get_note_detail(note['noteId'], cookie, note.get('xsecToken', ''))
                if detail:
                    details[i] = detail
                time.sleep(1)
        print(f"✅ 成功抓取 {len(details)} 篇笔记详情", file=sys.stderr)

        # 筛选高互动笔记，抓取评论
        if details:
            def parse_count(v):
                """将 '1.2万' 等格式转为数字"""
                if isinstance(v, (int, float)):
                    return int(v)
                s = str(v).strip()
                if '万' in s:
                    return int(float(s.replace('万', '')) * 10000)
                try:
                    return int(s)
                except (ValueError, TypeError):
                    return 0

            # 按点赞数排序，取 TOP N
            ranked = sorted(details.items(),
                            key=lambda x: parse_count(x[1].get('likes', 0)),
                            reverse=True)
            top_indices = [idx for idx, _ in ranked[:top_n]]

            print(f"💬 对点赞 TOP{len(top_indices)} 笔记抓取评论...", file=sys.stderr)
            for idx in top_indices:
                note = notes[idx]
                print(f"  💬 [{idx+1}] {note['title'][:30]}...", file=sys.stderr)
                detail_with_comments = get_note_detail(
                    note['noteId'], cookie, note.get('xsecToken', ''),
                    fetch_comments=True
                )
                if detail_with_comments and detail_with_comments.get('comment_list'):
                    details[idx]['comment_list'] = detail_with_comments['comment_list']
                    print(f"     → 获取 {len(detail_with_comments['comment_list'])} 条评论", file=sys.stderr)
                else:
                    print(f"     → 未获取到评论（SSR 中可能未包含）", file=sys.stderr)
                time.sleep(1)
    else:
        print(f"⚠️  未配置 cookie，只能抓取标题和点赞数据", file=sys.stderr)

    if output_format == 'json':
        # JSON 输出用于 Web 集成
        result = {
            'user': user_info,
            'notes': [],
        }
        for i, note in enumerate(notes):
            entry = {**note}
            if i in details:
                entry['detail'] = details[i]
            result['notes'].append(entry)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        report = generate_markdown(user_info, notes, details)
        print(report)

if __name__ == '__main__':
    main()
