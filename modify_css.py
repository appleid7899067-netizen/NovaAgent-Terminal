#!/usr/bin/env python3
"""Change the background color of .user-bubble in the requested chat.css."""
from pathlib import Path
import re
import sys

TARGET = Path("/data/data/com.termux/files/home/NovaAgent-Clean/channel/web/static/CSJS/css/chat.css")
NEW_COLOR = "#8B0000"


def main() -> int:
    if not TARGET.is_file():
        print(f"ERROR: target file does not exist: {TARGET}", file=sys.stderr)
        return 1

    original = TARGET.read_text(encoding="utf-8")
    selector = re.compile(r"(?ms)(^\s*\.user-bubble\s*\{)(.*?)(^\s*\})")
    matches = list(selector.finditer(original))
    if not matches:
        print("ERROR: no standalone .user-bubble rule found; file was not modified")
        return 2

    match = matches[0]
    block = match.group(0)
    background = re.compile(r"(?m)^(\s*background(?:-color)?\s*:\s*)([^;]+)(;)")
    if not background.search(block):
        print("ERROR: .user-bubble rule has no background/background-color declaration; file was not modified")
        return 3

    updated_block = background.sub(lambda m: f"{m.group(1)}{NEW_COLOR}{m.group(3)}", block, count=1)
    updated = original[:match.start()] + updated_block + original[match.end():]
    if updated == original:
        print("ERROR: replacement made no change; file was not modified")
        return 4

    TARGET.write_text(updated, encoding="utf-8")
    print(f"SUCCESS: updated {TARGET}")
    print(updated_block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
