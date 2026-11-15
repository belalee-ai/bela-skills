---
name: bela-content-planner
description: >
  AI content creator onboarding and planning hub. Use when the user says
  "set up my profile", "update my info", "content planning", "what can this plugin do",
  "help me plan content", or when no creator profile exists yet.
  Also triggers on first-time use of any other skill in this plugin.
  Collection: bela-skills.
---

# Content Planner — Onboarding & Router

This is the entry point for the bela-content-creator plugin. Two responsibilities:

1. **Onboarding** — create and maintain the creator profile
2. **Guidance** — help users understand which skill to use

## Onboarding

Check if `shared/creator-profile.md` exists in the user's working directory.

### If profile does NOT exist → run first-time setup

Present this to the user:

```
Welcome! I need to know a bit about you to personalize your briefings and topic recommendations.
3 questions, 30 seconds:

1. What's your professional background? What experiences give you a unique content angle?
   Example: former product manager / designer turned AI creator / bilingual with access to international sources

2. What's your main content platform and format?
   Example: Xiaohongshu short video / Douyin talking-head / YouTube long-form / WeChat articles

3. Which regions' AI news do you want to follow?
   A. 🌍 Both domestic + international (recommended)
   B. 🇨🇳 Domestic only (36kr, Huxiu, Xiaohongshu, Jike, domestic LLMs)
   C. 🌏 International only (TechCrunch, The Verge, Product Hunt, X/Twitter, Reddit, HN)
```

After receiving answers, generate `shared/creator-profile.md` with this structure:

```yaml
onboarding_complete: true
name: [user name]
background:
  career: [career history, listed item by item]
  skills: [capability tags, e.g., growth hacking, data analysis, bilingual]
  collaborators: [people who can help, e.g., boyfriend - frontend engineer]
  differentiators: [information advantages, e.g., reads English sources, cross-border experience]
platform:
  primary: [main platform, e.g., Xiaohongshu]
  secondary: [secondary platforms]
  formats: [content formats, e.g., talking-head short video, image-text posts]
news_sources: [A/B/C selection]
content_constraints:
  max_duration: [e.g., 2 minutes]
  style: [e.g., beginner-friendly, no jargon]
  avoid: [topics to avoid]
```

### If profile exists → skip onboarding

Read the profile and proceed with the user's request.

### Profile updates

When the user says "update my info", "change my platform", or similar — read the current profile, ask what to change, update the relevant fields only.

## Skill Guidance

When the user asks a general question like "what can you do" or "help me plan content", explain the three available skills:

- **Daily Briefing** — "日报" / "daily briefing" / "today's AI news" → A 1-minute scan of everything happening in AI today. Reports, policy, industry trends, product launches. Pure information, no topic recommendations.

- **Topic Picker** — "选题" / "topics" / "what should I post this week" → 3-5 scored topic recommendations for the week, with competitor analysis and unique angle suggestions based on your profile.

- **Video Topics** — "视频选题" / "video topics" / "give me scripts" → 5-8 evergreen video topics with ready-to-read 2-minute scripts. Focused on real user scenarios, not tech concepts.

## Shared Principles

All skills in this plugin follow these rules:

1. **User-scenario first** — topics must start from real user needs (save time, save money, fun, useful), never from abstract tech concepts
2. **Creator profile drives personalization** — unique angles, scoring, and recommendations all reference the profile's specific capability tags
3. **Source attribution required** — every news item needs a link + credibility marker (🟢 official / 🟡 reliable media / 🔴 unverified)
4. **No fabrication** — if a search returns nothing, say so. Never make up results.

## Content Compliance Rules

- Only recommend AI tools that are available domestically (for CN-based creators)
- Avoid discussing "AI replacing humans" narratives
- Avoid sensitive political framing around AI competition between countries
- Note: Xiaohongshu requires AI content labeling (since Feb 2026)
