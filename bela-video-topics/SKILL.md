---
name: bela-video-topics
description: >
  AI video topic generator with ready-to-read 2-minute scripts. Use when the user says
  "视频选题", "这周拍什么", "给我找视频选题", "脚本", "video topics", "give me scripts",
  "what should I film", or "video content ideas". Generates 5-8 evergreen video topics,
  each with a complete talking-head script. Topics must be user-scenario-driven, not
  tech-concept-driven. Prioritizes evergreen value over hot takes.
  Collection: bela-skills.
---

# Video Topics + Script Workshop

Generate 5-8 video topics with complete 2-minute talking-head scripts. Every script should be ready to read on camera — pick it up and start filming.

## Core Principle

**Topics always start from real user needs, never from tech concepts.**

Users care about: can it help me save time? Is it fun? Can it save money? Will it make me look smart?

They do NOT care about: "multi-model architecture", "agent workflows", "RAG retrieval augmentation".

❌ Wrong (tech-first):
- "Copilot multi-model review" → users don't know what multi-model means
- "AI Agent automation workflow" → too abstract, no personal relevance
- "LLM hallucination analysis" → too academic

✅ Right (user-scenario-first):
- "Use AI to write your weekly report in 3 minutes" → efficiency, everyone needs this
- "I made AI negotiate for me and saved ¥200" → fun + savings, story-driven
- "I did this with AI before my interview and got the offer" → specific scenario, clear outcome
- "3 AI tools your coworkers are secretly using" → social currency, click-worthy

## Pre-check

1. Read `shared/creator-profile.md`. If missing, tell the user to run content-planner first.
2. Read the profile's production constraints (max duration, editing capability, speaking style).

## Production Constraints

Read these from the creator profile. Defaults for new creators:

| Constraint | Meaning |
|-----------|---------|
| Video ≤ 2 min | Script ≤ 350 words (~100 sec talking pace), leave room for screen transitions |
| Beginner editing | Can do: screen recording + voiceover, talking head + subtitles, screenshot slideshow + narration. Cannot do: fancy edits/effects/animation |
| Practicing speaking | Scripts must be conversational, short sentences, each ≤ 25 characters. No stiff written language |
| Limited capacity | Research to final cut takes time. Provide 5-8 options but creator picks based on their schedule |
| No hot-take chasing | Topics must work "this week and next week". Timeliness is NOT a bonus |

## Execution

### Step 1: Source Material

**Auto mode (preferred):** Scan the working directory for recent `每日资讯*.md` or `AI资讯日报*.md` files (last 7 days). Use the news as raw material — abstract each news item into an evergreen topic.

Examples:
- News: "Claude had 3 days of outages" → Evergreen topic: "What to do when your AI tool suddenly breaks — you need a Plan B"
- News: "OpenAI proposes 4-day work week" → Evergreen topic: "Will AI take your job? An honest take from a product manager"
- News: "Microsoft Copilot adds multi-model" → Evergreen topic: "The 3 best AI office tools — I tested them all"

**Manual mode:** If no briefing files exist, search with WebSearch:
- `"AI tools" beginner guide this week`
- `"AI工具" 实测 小红书 本周`
- `"AI productivity" tips this week`

**Evergreen pool (fallback):** Always-viable directions when fresh material is thin:
- "How a PM picks AI tools" series (different scenarios: copywriting, PPT, data analysis, translation)
- "AI tool red flags" series (free vs paid, Chinese language support, reliability)
- "I tried AI for XX" personal experience series
- "AI for non-tech people" series
- "AI + career" series (resume, interview prep, presentations, data analysis)

### Step 1.5: Competition Analysis

For each candidate topic, assess the competitive landscape on the creator's main platform.

**Search (3-5 WebSearch calls):**
- `小红书 "[topic keyword]" 博主 爆款` — volume and hit patterns
- `小红书 AI工具 测评博主 口播` — same-lane creators
- `抖音 小红书 AI教程 博主` — reference accounts

**For each candidate, assess:**

1. **Competition density (1-5 stars):** How much similar content exists?
   - ⭐ Very low: almost no one has covered this angle
   - ⭐⭐⭐ Medium: some content, not saturated
   - ⭐⭐⭐⭐⭐ Very high: red ocean, search results are flooded

2. **Differentiation space (1-5 stars):** Can the creator stand out?
   - Consider: real work experience, unique perspective, hands-on data, contrarian angle, information gap from international sources
   - Most people do image-text → talking-head video is itself differentiation
   - Most people list 10 tools → going deep on 1-2 is differentiation

3. **Hit content patterns:** What do successful pieces in this topic look like?
4. **Reference creators:** 2-3 mid-tier accounts (50K-100K followers) to benchmark against

**Competition → priority:** Blue ocean (⭐-⭐⭐) → priority boost. Red ocean (⭐⭐⭐⭐+) → needs ≥⭐⭐⭐ differentiation space or exclude.

### Step 2: Scoring

Pick up to 12 candidates. Score each using the creator profile.

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Evergreen value** | 25% | Will people still want to watch this in 3 months? |
| **User resonance** | 25% | Does it start from a real user scenario? Can a non-tech person understand and care? (See user perspective test below) |
| **Unique angle** | 20% | What can this creator offer that others can't? Must reference a specific profile tag. |
| **Production feasibility** | 15% | Can it be done with screen recording + voiceover or talking head + subtitles? |
| **Growth potential** | 15% | Will it attract new followers? Worth sharing/bookmarking? |

**User perspective test (for "User resonance" dimension):**

Four questions — the first two are hard gates:

1. Does the topic start from a user scenario or a tech concept? Tech concept → score 1, exclude.
2. Can the user immediately see "what does this have to do with me"? No → score 1, exclude.
3. Does it require explaining jargon? (RAG, token, fine-tune, API, Agent, multimodal) → deduct points.
4. "I saw a video about..." test — would a friend say "oh tell me more" or "what does that mean"?

**5/5:** "My mom could understand it, find it useful, and want to share it with coworkers"
**3/5:** "Young people interested in AI can follow along, but wouldn't search for it"
**1/5:** "Only tech circles are discussing this, normal people don't relate"

**Filters:**
- User resonance ≤ 2 → exclude regardless of other scores
- Time-sensitive (expires in a week) → exclude unless abstractable to evergreen
- Pure technical explainer → exclude
- Red ocean (⭐⭐⭐⭐+) without ≥⭐⭐⭐ differentiation → exclude
- Requires fancy editing/special equipment → exclude
- Total score < 3.0 → exclude

Take **top 5-8** for scripts. Keep 2 extras as backup.

### Step 3: Write 2-Minute Scripts

Core deliverable. Each topic gets a complete, ready-to-read talking-head script.

**Script specs:**
- Total: 300-350 words (~100 seconds)
- Structure: Hook (10 sec) → Core (70 sec) → Wrap-up (20 sec)
- Language: conversational, short sentences, each ≤ 25 characters
- Banned: formal written language, long attributive clauses, parenthetical notes, unexplained English abbreviations

**Script template:**

```
[0-10 sec | Hook]
(Grab attention within 5 seconds. Use one of:)
(① Counterintuitive: "Did you know that XXX actually XXX")
(② Data shock: "XX% of people don't know that XXX")
(③ Pain point: "Have you ever dealt with XXX?")
(④ Suspense: "Today I'll tell you something about AI that might change how you work")

[Actual script lines, 2-3 sentences]

---

[10-80 sec | Core content]
(Split into 2-3 points, each a short paragraph. Mark screen transitions.)

Point 1: [Subheading]
[Script lines, 4-6 sentences]

📷 Visual suggestion: [screen recording / screenshot / talking head]

Point 2: [Subheading]
[Script lines, 4-6 sentences]

📷 Visual suggestion: [screen recording / screenshot / talking head]

---

[80-100 sec | Wrap-up]
(One-line summary + engagement prompt. Be specific, not generic "follow me".)

[Script lines, 2-3 sentences]
[Engagement: ask a specific question for comments]
```

**If a script isn't working:** If a topic is hard to explain in 350 words or has no good hook, abandon it and swap in a backup from Step 2. Don't force a mediocre script.

**Script quality checklist:**
- [ ] 300-350 words total?
- [ ] First sentence grabs attention within 5 seconds?
- [ ] No sentences over 25 characters?
- [ ] No stiff/formal language? Read it aloud — does it flow?
- [ ] Core split into 2-3 clear points?
- [ ] Visual suggestions are achievable (screen recording / screenshot / talking head)?
- [ ] Engagement prompt is a specific question, not "remember to follow"?

### Step 4: Output

Filename: `视频选题_YYYY年M月D日.md`

Include for each topic: overview table → detailed card with scores, competition analysis, 3 title options, full script, production notes, source links.

End with: competition landscape summary, filming priority recommendation, excluded candidates with reasons.

### Step 5: Save

1. Save to working directory
2. Update `README.md` navigation

## Compliance (reference `references/compliance-rules.md`)

Detailed compliance rules for domestic tool recommendations, Xiaohongshu AI labeling, and sensitive topic avoidance are in the references directory.

## Topic Red Lines

Never recommend:
- Tech-concept-first topics (the #1 red line)
- Topics too abstract for users to see personal relevance
- Pure technical explainers
- Content requiring advanced editing/special equipment
- AI ethics / politically sensitive topics
- Unverified rumors only
- Pure hot takes that expire in a week
