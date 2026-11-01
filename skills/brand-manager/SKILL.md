---
name: brand-manager
description: Manage brand identity for NovaAgent. Use when user asks about brand name, colors, logos, or wants to switch branding.
metadata:
  cow:
    emoji: 🎨
---

# Brand Manager

## Get Brand Info

Read `branding/brand_config.json`.

## Switch Brand

1. Inspect the actual brand configuration source and supported fields in the project before changing anything. In this repository, `common/branding.py` reads `branding/brand_config.json` when present and otherwise falls back to environment variables/default values; it does not currently enumerate `brands/`.
2. Check whether the requested configuration or brand directory exists. If not, explain the current default and do not invent a switch mechanism.
3. Before an approved replacement, preserve a recoverable copy, verify the target path, and keep secrets out of output. Do not overwrite unrelated files.
4. Apply only the requested change. Restart only when required and authorized; otherwise tell the user a restart is needed.
5. Verify non-sensitive effective values through the application or rendered UI. Report checks not performed.

## Show Current Brand

Read `branding/brand_config.json` and report non-sensitive brand fields only. Never dump credentials or unrelated configuration values.

## Triggers

Use when the user asks which NovaAgent brand is active, requests brand identity details, or asks to change brand name, colors, logos, or configuration.

