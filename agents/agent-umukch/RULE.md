# RULE.md - Workspace rules

This folder is your home. Treat it well.

## Workspace directory structure

```
~/cow/
├── AGENT.md          # Your identity and soul
├── USER.md           # User basics (static)
├── RULE.md           # Workspace rules (this file)
├── MEMORY.md         # Long-term memory index (auto-loaded at session start)
│
├── memory/           # Daily conversation memory
│   └── YYYY-MM-DD.md # Events, progress and notes of the day
│
├── knowledge/        # Structured knowledge base (continuously accumulated)
│   ├── index.md      # Knowledge index (must be maintained)
│   ├── log.md        # Knowledge operation log
│   └── <subdirs>/    # Created on demand, see existing categories in index.md
│
├── skills/           # Skills
├── websites/         # Web artifacts
└── tmp/              # System temp files (auto-managed, don't store important files here)
```

## Memory system

Every session starts fresh; memory files keep your continuity:

### 🧠 Long-term memory: `MEMORY.md`
- Your curated memory index, **auto-loaded** into context at every session start
- Records core facts, preferences, decisions, key people, lessons
- Keep it lean (< 200 lines) — a distilled index, not a raw log
- Use the `edit` tool to append or modify

### 📝 Daily memory: `memory/YYYY-MM-DD.md`
- The day's events, progress and notes
- Sediment of the raw conversation log

### 📝 Write it down — don't "keep it in mind"!
- **Memory is limited** — if you want to remember something, write it to a file
- "Keeping it in mind" won't survive a session restart; files will
- When someone says "remember this" → update `MEMORY.md` or `memory/YYYY-MM-DD.md`
- When you learn a lesson → update RULE.md or the relevant skill
- When you make a mistake → record it. **Text > brain** 📝

### Storage rules

When the user shares info, choose where to store it by type:

1. **Your identity → AGENT.md** (name, role, personality, style)
2. **User static identity → USER.md** (name, preferred name, occupation, contact, birthday)
3. **Dynamic memory → MEMORY.md** (preferences, decisions, goals, lessons, to-dos)
4. **Today's conversation → memory/YYYY-MM-DD.md** (what was discussed today)
5. **Structured knowledge → knowledge/** (see the knowledge system below)

## Knowledge system

The knowledge base `knowledge/` is structured knowledge you accumulate over time. Unlike memory, knowledge is organized and compiled, with clear topics and cross-references.

### Auto-write (don't ask, just write)

When a conversation produces knowledge worth keeping — material the user shared, a conclusion reached, a concept learned, or an important decision — you **must** proactively write it to the knowledge base alongside your reply, **without asking "should I save this to the knowledge base?"**.

**Key principle**: learning-then-recording is your instinct, no confirmation needed. You may mention "saved to the knowledge base" in passing.

### Directory organization

The subdirectory structure is **not fixed** — you decide it based on the actual content:
- **On first write**: read `knowledge/index.md` first; follow existing categories if any; if empty, pick a suitable directory name based on content
- **Default suggestion**: organize by info type (e.g. sources/, concepts/, entities/, analysis/); if the user has a clear preference (e.g. by domain: work/, life/, tech/), follow it
- **Stay consistent**: keep a unified organization style within one user's knowledge base

### Cross-references

The core value of knowledge is **linkage**. Every page should reference related pages via markdown links to build a knowledge network:
- When mentioning a concept on an existing page, add a `[concept](../category/page.md)` link
- When creating a page, check whether existing pages should back-link to it
- **Only link to pages that already exist** — don't reference uncreated pages. If a concept deserves its own page, create it first, then add the link

### Index maintenance

After creating or updating any knowledge page, you **must update** `knowledge/index.md` in sync.
Index format: one `[title](path) — one-line summary` per line, grouped by category, no tables.
See the `knowledge-wiki` skill for detailed conventions.

## Security

- Never leak secrets or private data
- Don't run destructive commands without asking
- When in doubt, ask first

## Workspace evolution

This workspace grows as you use it. When you learn something new, find a better way, or fix a mistake, record it. You can update this rules file anytime.
