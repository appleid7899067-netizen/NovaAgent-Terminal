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
## Duplicate skill installation prevention
- Policy: from now on, any attempt to install or register a new skill will be checked against existing skills to prevent duplicates.
- Guard: a dedicated guard script (guard_duplicate_install.py) will be invoked before installation to detect duplicates.
- If a duplicate is detected, installation will abort with a clear message and no changes will be applied.
- Script location: /data/data/com.termux/files/home/projects/NovaAgent-Brandable/cowbase/skills/guard_duplicate_install.py
- How to use:
  - Run the guard with the target skill name, e.g. python3 /data/data/com.termux/files/home/projects/NovaAgent-Brandable/cowbase/skills/guard_duplicate_install.py --name <skill-name>
  - If output contains DUPLICATE, do not proceed with installation. If OK, proceed.
- Logging: duplicate attempts should be logged in the project log as part of knowledge base for traceability.


## Rule: Skill Installation Guard
1. **Never** overwrite an existing skill without explicit confirmation.
2. Use the wrapper `install_with_guard.sh <skill-name>` for standard installs.
3. Use `install_with_guard.sh <skill-name> --update` to safely upgrade existing skills (auto-backups are created in `guard_backups/`).

## Rule: File Writing & Escaping
1. **NEVER** output raw `\n` or escape characters into a file.
2. When using the `write_file` or `bash` tool to create code (Python, HTML, JS), always use **Heredoc** format (e.g., `cat << 'EOF' > file.py`) in bash to avoid string escaping issues.
3. If using JSON payloads to write files, ensure newlines are properly escaped as actual line breaks, not literal `\n` text.
4. Always verify the file content by reading it immediately after writing. If literal `\n` characters are found in the code, delete the file and rewrite using the Heredoc method.

## Rule: Premium UI/UX Design Standard
1. **Never generate plain HTML.** Every UI must look like a modern SaaS product (e.g., Linear, Vercel, Apple).
2. **Color Palette:** Use a dark theme by default (`#0f0f0f` background, `#1e1e1e` surface, `#a78bfa` primary accent, `#e2e8f0` text).
3. **Typography:** Always include Google Fonts: `Inter` for English and `Noto Sans Thai` for Thai.
4. **Layout:** Use CSS Grid or Flexbox. Center content properly. Add padding (min 16px) and gap between elements.
5. **Micro-interactions:** Always add `transition: all 0.2s ease` to buttons and links. Add `hover` states.
6. **Borders & Shadows:** Use `border: 1px solid rgba(255,255,255,0.1)` and `box-shadow: 0 4px 20px rgba(0,0,0,0.5)` for cards.
7. **Icons:** Use FontAwesome (`<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">`) for icons.

## Rule: Senior Software Engineer Standard (Codex Mode)
1. **Think First:** Always output a brief 3-step plan in Markdown before writing code for a complex task.
2. **Error Handling:** Never write a function without a `try/except` (Python) or `try/catch` (JS) if it involves I/O, network, or parsing.
3. **Code Structure:** Separate concerns. E.g., in FastAPI, separate Pydantic models from route handlers.
4. **Read Before Write:** If modifying an existing file, use `read_file` first to understand the current context.
5. **Format:** Always put code inside Markdown blocks (```python, ```html) in the chat. When using tools to write files, ensure 100% valid syntax.

## Rule: Mobile Responsive Design (CRITICAL)
1. **ALWAYS** use CSS Grid or Flexbox with `flex-wrap: wrap` for card layouts.
2. **NEVER** use fixed widths (e.g., `width: 1000px`). Use `max-width`, `%`, or `fr` units.
3. On mobile screens (`@media (max-width: 768px)`), collapse sidebars and stack cards vertically.
4. Add `<meta name="viewport" content="width=device-width, initial-scale=1.0">` in the `<head>` of EVERY HTML file.

## Rule: String Escaping (Double Check)
1. If writing HTML/JS/Python, **NEVER** output the literal characters `\n` at the beginning of the file or inside text nodes.
2. Use the Bash `cat << 'EOF' > file.html` method strictly for creating files to avoid JSON string escaping.
