#!/usr/bin/env python3
"""
Browser SlilelO Skill — Example Playwright automation script.
Released by SlilelO boss (โครตโกง).

Usage:
    python scripts/browser_automation.py --url http://localhost:3000
"""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright


def run(url: str, output: str = "/tmp/browser-slilelo-screenshot.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="th-TH",
        )
        page = context.new_page()

        print(f"[SlilelO] Navigating to {url}")
        page.goto(url, wait_until="networkidle")

        # Take full-page screenshot
        page.screenshot(path=output, full_page=True)
        print(f"[SlilelO] Screenshot saved to {output}")

        # Print page title for verification
        print(f"[SlilelO] Page title: {page.title()}")

        # Dump ARIA tree (first 2000 chars) for selector discovery
        tree = page.accessibility.snapshot()
        tree_str = str(tree)
        print(f"[SlilelO] ARIA snapshot (truncated): {tree_str[:2000]}")

        browser.close()
    return output


def main():
    parser = argparse.ArgumentParser(description="Browser SlilelO automation")
    parser.add_argument("--url", default="http://localhost:3000", help="Target URL")
    parser.add_argument(
        "--output",
        default="/tmp/browser-slilelo-screenshot.png",
        help="Screenshot output path",
    )
    args = parser.parse_args()

    run(args.url, args.output)


if __name__ == "__main__":
    main()
