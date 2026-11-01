---
name: live-slot-fetch
description: Fetch live slot game results from a provided URL using browser tooling; supports login-protected pages and returns structured results for recording and analysis.
license: Complete terms in LICENSE.txt
---

# Live Slot Fetch Skill

This skill provides a lightweight, reusable workflow to retrieve live slot game results from a URL. It is designed to work with a browser tool on the host machine, handle simple login-protected pages, and emit a structured JSON summary that can be stored in knowledge or logs.

## When to Use
- You have a URL to a live slot game results page and want to capture the latest spin data (reels, payout, bankroll).
- The page may require a browser rendering step or JavaScript loading; this skill will attempt to fetch the HTML and extract the latest known spin data.
- You want to record results for auditing, strategy testing, or knowledge propagation.

## Bundled Resources
- scripts/fetch_live_slot.py: Core script to fetch and parse live slot results.

## Using the Skill
Prerequisites:
- ใช้ MCP `slilelo-browser` แทน (ไม่ต้องติดตั้ง cow)

Usage:
- Run the fetch script with a URL and optional output path
  - python3 <skill-base>/scripts/fetch_live_slot.py --url "<slot-game-url>" --output <path/to/output.json>
- If you omit --output, results are printed to stdout as JSON

Example:
- python3 /data/data/com.termux/files/home/cow/skills/live-slot-fetch/scripts/fetch_live_slot.py --url "https://example.com/slot" --output /tmp/slot_latest.json

Output:
- A JSON object containing at least:
  - success: true/false
  - timestamp: UNIX epoch of fetch
  - latest_spin: array describing the reels if parsed, or raw_html_snippet as fallback
  - snippet: a short HTML snippet or raw relevant data for reference

Notes:
- This is a lightweight, heuristic-based fetcher. If the page structure is complex or requires login, the script will report an error and provide the raw content for manual inspection.

## Updating and Validation
- After fetching, you can feed the results into knowledge: knowledge/log.md or knowledge/index.md as needed.
- Validate the output JSON with a quick-check script if desired.

## Triggers
- Describe trigger keywords and usage here.


## Body
- Describe core capabilities and usage here.


## Resources
- scripts/, references/ (optional)

