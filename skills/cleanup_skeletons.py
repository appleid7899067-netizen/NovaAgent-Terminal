#!/usr/bin/env python3
import json, sys
from pathlib import Path

def filter_entries(obj):
    if not isinstance(obj, dict):
        return obj, 0
    to_delete = []
    for k, v in list(obj.items()):
        desc = str(v.get('description',''))
        if 'Skeleton placeholder' in desc or 'skeleton placeholder' in desc:
            to_delete.append(k)
    for k in to_delete:
        del obj[k]
    return obj, len(to_delete)


def process_file(path: Path):
    if not path.exists():
        print(f"NOTFOUND: {path}")
        return 0
    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print(f"WARNING: {path} does not contain a top-level object; skipping")
        return 0
    new_data, removed = filter_entries(data)
    with path.open('w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    return removed


def main():
    paths = sys.argv[1:]
    if not paths:
        print("Usage: cleanup_skeletons.py <json_path> [<json_path> ...]")
        sys.exit(1)
    total_removed = 0
    for p in paths:
        removed = process_file(Path(p))
        total_removed += removed
        print(f"Processed {p}: removed {removed} skeleton placeholders")
    print(f"TOTAL_REMOVED={total_removed}")

if __name__ == '__main__':
    main()
