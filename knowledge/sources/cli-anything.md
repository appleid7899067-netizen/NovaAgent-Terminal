---
title: CLI-Anything project overview
url: https://github.com/HKUDS/CLI-Anything
---

CLI-Anything is an open-source project by HKUDS that converts desktop software and source code into a set of command-line interfaces (CLIs) with a REPL mode and JSON output. This enables AI agents like Claude Code, Cursor, Codex, or OpenClaw to control real software via CLI without relying on screenshots or GUI interactions.

Two main components:
- CLI-Hub: a repository and registry hub installed via pip install cli-anything-hub. It aggregates 79 ready-made CLIs in the main registry and 24 CLIs contributed by the community (e.g., GIMP, Blender, Inkscape, Audacity, LibreOffice, OBS Studio, Kdenlive, Shotcut, FreeCAD, QGIS, Calibre, Obsidian).
- cli-anything plugin: for agents to analyze source code and automatically generate new CLIs through a 7-phase pipeline, including design, code (Python Click) with Undo/Redo, tests, and skill file generation. It supports a unified skills system so agents can call newly created CLIs.

License and date:
- Apache 2.0 license
- Opened to the public around March 2026, with thousands of stars and active development (as of the README).

Key concepts:
- Agent-native software: turning software into programmable CLI tasks.
- JSON-friendly outputs: structured data to be consumed by agents.
- REPL and scripting: interactive development and automation.
- SKILL.md generation: automatic creation of agent-readable skill definitions for each CLI harness.

Next steps (recommended):
- Explore CLI-Hub to discover available CLIs and try installing a few to experience the workflow.
- If you want a new harness, run the 7-phase harness generator on a target software and review the resulting SKILL.md.
- Use the REPL to interact with CLIs and test automation pipelines.

Notes:
- The project emphasizes agent-first design and scalable expansion of CLI coverage across many domains.