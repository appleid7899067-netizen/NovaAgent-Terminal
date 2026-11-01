#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path('/data/data/com.termux/files/home/projects/NovaAgent-Brandable/cowbase/skills')
# Try to create backup dir in /tmp first; fallback to project tmp if needed
try:
    BACKUP_ROOT = Path('/tmp/skill-backups')
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
except Exception:
    BACKUP_ROOT = Path('/data/data/com.termux/files/home/projects/NovaAgent-Brandable/cowbase/tmp/skill-backups')
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)


def ensure_sections(text: str) -> str:
    # detect existing sections
    has_triggers = bool(re.search(r'^\s*##\s*Triggers\b', text, re.MULTILINE | re.IGNORECASE))
    has_body = bool(re.search(r'^\s*##\s*Body\b', text, re.MULTILINE | re.IGNORECASE))
    has_resources = bool(re.search(r'^\s*##\s*Resources\b', text, re.MULTILINE | re.IGNORECASE))

    additions = []
    if not has_triggers:
        additions.append('\n## Triggers\n- Describe trigger keywords and usage here.\n')
    if not has_body:
        additions.append('\n## Body\n- Describe core capabilities and usage here.\n')
    if not has_resources:
        additions.append('\n## Resources\n- scripts/, references/ (optional)\n')

    if additions:
        return text.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'
    return text


def backup_file(path: Path) -> Path:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = BACKUP_ROOT / (path.name + '_' + timestamp)
    path_text = path.read_text(encoding='utf-8', errors='ignore')
    backup_path.write_text(path_text, encoding='utf-8')
    return backup_path


def process_file(md_path: Path) -> tuple:
    try:
        content = md_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return (False, f'ERROR_READ {md_path}: {e}')
    new_text = ensure_sections(content)
    if new_text != content:
        backup = backup_file(md_path)
        md_path.write_text(new_text, encoding='utf-8')
        return (True, f'UPDATED {md_path} (backup {backup})')
    return (False, f'NO_CHANGE {md_path}')


def main():
    results = []
    for md in ROOT.rglob('SKILL.md'):
        if md.is_file():
            changed, msg = process_file(md)
            results.append(msg)
    print('\n'.join(results))

if __name__ == '__main__':
    main()
