---
name: bela-skill-hygiene
description: Use when installing new skills, auditing existing skills for overlap, or managing skill count to prevent prompt bloat and selection accuracy degradation。收录于 bela-skills。
argument-hint: "[audit | check <description> <name>]"
---

# Skill Hygiene

Audit installed skills in Claude Code or Codex. Detect overlaps, audit bloat, prevent prompt pollution.

## Core Principles

1. **Fewer, sharper skills** — Every skill in the prompt competes for the model's attention. Beyond ~30, selection accuracy drops.
2. **Overlap is noise** — Two skills with similar descriptions confuse the model about which to invoke.
3. **Domain scoping** — Plugins like Vercel or Figma belong at project-level, not global.
4. **Soft delete, hard data** — Archive skills instead of deleting. Track decisions in a log.

## When to Use

- **Before installing a new skill** — run duplicate check to catch overlap
- **When user mentions skill quality issues** ("wrong skill triggered", "confused selection") — run full audit
- **Periodically** — suggest audit when skill count appears high

## Commands

Use `${CLAUDE_SKILL_DIR}` to reference the script path (this is a built-in variable that resolves to this skill's directory at runtime):

### Duplicate Check (pre-install)

**ABSOLUTE RULE: Run this BEFORE every new skill install.**

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/skill-audit.sh" --check-duplicate "<description of new skill>" "<skill-name>"
```

Show the overlap results to the user. If overlap >= 70%, recommend replacing the existing skill instead of installing both.

### Full Audit

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/skill-audit.sh"
```

Produces a 5-section report:
1. Installed custom skills — name, line count, directory size, file count
2. Overlap analysis — pairwise keyword comparison (stopword-filtered, two-pass stemming)
3. Enabled plugins — from settings.json with estimated prompt impact
4. Health warnings — oversized directories, bundled deps, missing descriptions
5. Archived skills — soft-deleted, recoverable

### Audit a Codex directory

```bash
skill_dir="$HOME/.agents/skills/bela-skill-hygiene" # Adjust to this skill's installation path.
audit_root="$HOME/.agents/skills" # Or "$HOME/.codex/skills" for legacy entries.
SKILLS_DIR="$audit_root" SETTINGS_FILE=/dev/null AUDIT_LOG="$HOME/.codex/skills-audit.log" \
  bash "$skill_dir/scripts/skill-audit.sh"
```

For a project, set audit_root to its .agents/skills directory. For a duplicate check, append --check-duplicate "<description>" "<name>" to the script command. The script audits one directory per run and compares English keywords. Its plugin report and hook example are specific to Claude Code.

### Archive a Skill

```bash
mv ~/.claude/skills/<name> ~/.claude/skills/.archived-<name>
```

Restore anytime by removing the `.archived-` prefix. For Codex, move the selected entry outside all scanned skills directories so it can be restored to its original location. Check whether it is a link before moving the underlying files.

## Thresholds

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Total skills in prompt | < 30 | 30–50 | > 50 |
| Pairwise keyword overlap | < 40% | 40–69% | >= 70% |
| Skill directory size | < 5 MB | 5–10 MB | > 10 MB |
| Files per skill directory | < 20 | 20–50 | > 50 |

## Anti-Patterns

| Anti-Pattern | Why It's Bad | What to Do Instead |
|---|---|---|
| Installing every skill you find | Prompt bloat, selection confusion | Run duplicate check first, install only what you'll use |
| All plugins enabled globally | 30+ irrelevant skills per conversation | Move domain plugins to project-level settings |
| Merging pipeline skills | Breaks specialized prompts (e.g., scriptwriter → storyboard → animator) | Keep pipeline stages separate; only merge truly redundant skills |
| Deleting skills permanently | Can't recover if you need them later | Archive with `.archived-` prefix |
| Ignoring missing descriptions | Model can't match skills without descriptions | Ensure every SKILL.md has a clear `description:` in frontmatter |

## Strategy: Global vs Project-Level

```
~/.claude/settings.json          → Core workflow skills (used in every project)
.claude/settings.json            → Domain plugins (Vercel, Figma, etc.)
.claude/settings.local.json      → Same, but git-ignored (personal preferences)
```

## Claude Code Hook Integration (optional)

Auto-remind before skill installs. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'npx skills (add|remove|update)|skills add|skills remove'; then echo '[user-prompt-submit-hook] Run skill-hygiene duplicate check before proceeding.'; fi"
          }
        ]
      }
    ]
  }
}
```

## Supporting Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `scripts/skill-audit.sh` | Core audit script (bash 3+ compatible) | When running any audit command |
