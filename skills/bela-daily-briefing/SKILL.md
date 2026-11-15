---
name: bela-daily-briefing
description: >
  Daily industry briefing for content creators. Use when the user says
  "日报", "今日简报", "daily briefing", "today's news", "每日资讯",
  "what happened today", or "news roundup". Outputs a pure information
  digest — no topic selection, no scoring, no scripts.
  Collection: bela-skills.
---

# Daily Briefing

Generate a full-landscape industry digest for the user's domain. Pure information — no topic recommendations, no scoring, no action plans.

## First-Use Setup

Read `shared/creator-profile.md`. If it does not exist, create it by asking:

1. **What domain do you cover?** (e.g., AI, crypto, indie hacking, marketing tech, design tools)
2. **What's your professional background?** List career experiences and unique skills that differentiate your content.
3. **What platforms do you publish on?** Primary platform + secondary. What format? (short video, long-form, image-text, newsletter)
4. **Which regions' news do you want?** Domestic only / international only / both
5. **What language should output be in?** (中文 / English / bilingual)

Save answers to `shared/creator-profile.md` as structured YAML. Mark `onboarding_complete: true`.

If profile already exists, read it and proceed.

## What to Search

Build search queries dynamically from the profile. **Do not use hardcoded search terms.**

Read `profile.domain` and `profile.news_sources` to construct searches:

**Template — international sources (4-6 searches):**
- `"[domain] news today"` — general roundup
- Top 3 companies/products in the domain + `"announcement"` or `"update"` — major player moves
- `"[domain] product launch"` + date filter — new products
- `"[domain] tools trending"` — ecosystem updates

**Template — domestic sources (3-4 searches):**
- `"[domain] 今日热点"` or `"[domain] 最新消息"` — general roundup
- Key domestic players in the domain + `"最新"` — major player moves
- `"[domain] 政策"` or `"[domain] 行业趋势"` — policy & industry

**Template — full-landscape supplement (2-3 searches):**
- `"[domain] report [year]"` or `"[domain] industry report"` — reports & research
- `"[domain] regulation"` or `"[domain] policy [year]"` — regulatory moves
- `"[domain] research breakthrough"` — academic progress

Only run the source groups that match `profile.news_sources` (domestic / international / both).

**Per-item record:** title + summary (≤ 1 short sentence) + source link + publish date + credibility (🟢 official / 🟡 reliable media / 🔴 unverified)

**Fallbacks:** Bad results → skip. Under 4 international or 3 domestic items → try alternate phrasing. Total < 8 → mark "⚠️ Limited data today".

## How to Classify

Sort results into 5 sections:

1. **Reports & Trends** — major reports, research findings, funding (detailed: 2-4 sentences each)
2. **Policy & Regulation** — regulatory moves (detailed: 2-4 sentences each)
3. **Industry Developments** — technology, commercialization, ecosystem (detailed: 2-4 sentences each)
4. **International News** — table, one-line summaries
5. **Domestic News** — table, one-line summaries

Deep items → first three sections. Quick hits → two table sections. No item in multiple sections. If a section has nothing, note "No major updates today" instead of omitting it.

## Output

Filename pattern from profile's language preference:
- Chinese: `每日资讯_YYYY年M月D日.md`
- English: `daily-briefing_YYYY-MM-DD.md`

Structure: title with date → tagline → 5 sections as above → credibility legend → generation timestamp → one-line pointer to topic-picker skill.

Save to working directory. Update `README.md` navigation if it exists.

## History

Before searching, scan the last 3 days of briefing files in the working directory. Skip identical news unless there's a meaningful update — mark continuations "📎 Ongoing".

## Rules

- Every item needs a source link + credibility marker. No link = no entry.
- Cover the FULL landscape — not just content-worthy topics.
- Never fabricate. Search returns nothing → say so.
- No topic recommendations, scoring, or action plans. This skill is information only.
- Filler phrases ("worth watching", "drawing attention") → replace with concrete facts.
