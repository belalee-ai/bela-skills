# Daily Job Briefing

> [中文版](README.zh-CN.md)

A Claude Code skill that searches the latest job openings in your target city and industry every day, and delivers a personalized briefing with job recommendations, salary analysis, market trends, and an action checklist.

## Why This Skill?

Job seekers waste hours every day scrolling through multiple platforms, mentally filtering irrelevant listings, and losing track of positions they've seen. This skill solves that by acting as your personal job intelligence officer:

1. **You describe yourself once** — target city, industry, role, salary range, preferences — and a persistent profile drives all future searches
2. **It searches for you** — across company career pages, job platforms, LinkedIn, and industry media, using a 3-tier credibility system so you know what to trust
3. **It thinks for you** — every position is scored on 4 weighted dimensions against YOUR profile, not generic criteria
4. **It tells you what to do** — each briefing ends with a prioritized action checklist (P0/P1/P2), not just a list of links

The goal: open the briefing, spend 1 minute, know exactly what's worth applying to today.

## Features

- **Personalized Matching** — One-time onboarding (8 questions, ~3 min) builds your profile; all recommendations are tailored to your background
- **3-Tier Source Hierarchy** — Company career pages (high credibility) → Job platforms + LinkedIn (medium) → Industry media & communities (reference). Each position is tagged with its source tier so you know the confidence level
- **4-Dimension Scoring** (max 5.0) — Experience fit (35%) + Salary competitiveness (25%) + Growth potential (20%) + Preference match (20%). Positions are ranked into tiers: Tier 1 (≥4.0, max 5 picks) → Tier 2 (3.0–3.9) → Tier 3 (2.5–2.9)
- **6 Modes** — Full briefing / Quick briefing / Targeted tracking / History review / Bookmark tracking / Market overview
- **Bookmark System** — Say "bookmark XX" in chat to follow a position; supports 14-day smart decay and auto-archiving
- **Multi-Industry** — Pre-built company lists and search templates for AI, Internet, FinTech, Gaming, New Energy, and E-commerce
- **History Awareness** — Automatically checks the last 3 days of briefings to deduplicate, track status changes, and highlight what's genuinely new (🆕)

## How It Works

```
Onboarding (once)          Briefing (daily)
┌─────────────┐     ┌──────────────────────────────────────────┐
│ 8 questions  │     │ Step 1: Multi-source job collection      │
│ → profile    │────▶│ Step 2: Market trend scan                │
│   created    │     │ Step 3: 4D matching & scoring            │
│              │     │ Step 4: Generate structured briefing     │
│              │     │ Step 5: Save & index                     │
└─────────────┘     └──────────────────────────────────────────┘
```

**Step 1 — Job Collection**: Searches 3 tiers of sources (company pages → platforms → media) with a total cap of ~15 searches. Each position records: company, role, team/BU, city, salary, status, source link, source tier, and date.

**Step 2 — Market Scan**: Checks 4 dimensions (salary trends, supply/demand, hot directions, industry events) to surface signals that affect your search strategy.

**Step 3 — Matching & Scoring**: Every position is scored against your profile using the 4D weighted model. Matching analysis references your specific experience — not vague "you're a good fit" statements.

**Step 4 — Briefing Output**: Top 3 positions get deep analysis: why it matches (citing your experience), interview talking points (50–80 words), resume configuration advice, and specific delivery channel recommendations.

**Step 5 — Save & Navigate**: Briefing saved to `shared/reports/` with an auto-maintained index for easy history access.

## Installation

### Method 1: Skills CLI (Recommended)

```bash
npx skills add belalee-ai/bela-skills
```

### Method 2: Claude Code Plugin

```bash
/plugin marketplace add belalee-ai/daily-job-briefing
/plugin install daily-job-briefing
```

### Method 3: Ask Your Agent

Just tell Claude Code:

> Install the daily-job-briefing skill from https://github.com/belalee-ai/daily-job-briefing

Claude will handle cloning and setup automatically.

### Method 4: Manual Clone

```bash
git clone https://github.com/belalee-ai/daily-job-briefing.git ~/.claude/skills/daily-job-briefing
```

### Verify Installation

After installation, check that the skill is loaded:

```
~/.claude/skills/daily-job-briefing/
├── SKILL.md          ← Core instruction file (must exist)
├── templates/        ← Report & profile templates
├── references/       ← Search source configs
└── shared/           ← Runtime data (auto-created on first use)
```

No API keys or dependencies required. The skill works with Claude Code's built-in web search. For enhanced search capabilities, see [Optional Enhancements](#optional-enhancements).

## Usage

After installation, use these trigger phrases in Claude:

| Phrase | What it does |
|--------|-------------|
| "job briefing" / "any new jobs today" | Generate a full daily briefing |
| "quick briefing" / "tldr" | First-tier picks only, compact format |
| "any updates from XX company" | Track a specific company |
| "my bookmarks" / "track progress" | Check latest status of all bookmarked positions |
| "market overview" / "salary trends" | Dedicated market analysis |
| "update my profile" | Change target city / industry / salary preferences |

## Quality Standards

Every briefing enforces these rules automatically:

- **Completeness** — Each position must have 7 elements: company, role, team, city, salary, status, source link. Missing items are marked "TBC"
- **Salary credibility** — Tagged as ✅ official / ⚠️ estimated / ❓ unverified
- **No fabricated links** — Source URLs must come from actual search results; when unavailable, the platform name is cited instead
- **Honest matching** — Match analysis must cite specific experience from your profile; gaps are reported as-is, never inflated
- **Tier discipline** — Tier 1 is capped at 5 positions with a minimum 1.0-point gap from Tier 2
- **Risk transparency** — Negative company news (layoffs, losses) is surfaced with source attribution

## Optional Enhancements

- **Resume Matching** — Place your resume in `shared/resume/`; the briefing will reference your specific project experience for deeper matching analysis
- **Web Access Skill** — Install [web-access](https://github.com/eze-is/web-access) to unlock browser scraping and authenticated access for enhanced search

## Directory Structure

```
daily-job-briefing/
├── SKILL.md                        # Core instruction file
├── LICENSE.txt                     # MIT License
├── README.md                       # This file
├── templates/
│   ├── daily-job-report.md         # Briefing output template
│   ├── user-profile-template.md    # User profile template
│   └── bookmarks-template.md       # Bookmark format template
├── shared/                         # Runtime data (auto-generated, gitignored)
│   ├── user-profile.md             # Your profile (created after onboarding)
│   ├── bookmarks.md                # Bookmarked positions
│   ├── report-index.md             # Briefing index
│   ├── reports/                    # Generated briefings
│   └── resume/                     # Your resume (optional)
└── references/
    └── search-sources.md           # Industry search sources & keyword templates
```

## Data & Privacy

All runtime data is stored locally in `shared/` and excluded from git via `.gitignore`:

- `user-profile.md` — your job search profile
- `bookmarks.md` — bookmarked positions
- `resume/` — your resume files
- `reports/` — generated briefings

**Nothing is uploaded to any server.** If you fork or share this repo, make sure `shared/` contains no personal data.

## License

MIT
