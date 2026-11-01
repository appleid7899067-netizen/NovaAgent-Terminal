#!/usr/bin/env python3
import re
import json
from pathlib import Path

ROOT = Path('/data/data/com.termux/files/home/projects/NovaAgent-Brandable/cowbase/skills')

def scan_skill(md_path: Path):
    try:
        text = md_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return {
            'path': str(md_path),
            'ok': False,
            'error': str(e)
        }
    # extract name and description from front matter lines like:
    # name: something
    # description: something
    name_match = re.search(r'^\s*name\s*:\s*(.+)$', text, re.MULTILINE | re.IGNORECASE)
    desc_match = re.search(r'^\s*description\s*:\s*(.+)$', text, re.MULTILINE | re.IGNORECASE)
    name = (name_match.group(1).strip() if name_match else None)
    description = (desc_match.group(1).strip() if desc_match else None)

    # check skeleton placeholder in description
    skeleton = False
    if description and ('Skeleton placeholder'.lower() in description.lower() or 'skeleton placeholder'.lower() in description.lower()):
        skeleton = True

    # check for core sections in the markdown
    sections = {
        'Triggers': bool(re.search(r'^##\s*Triggers', text, re.MULTILINE)),
        'Body': bool(re.search(r'^##\s*Body', text, re.MULTILINE)),
        'Resources': bool(re.search(r'^##\s*Resources', text, re.MULTILINE)),
    }

    status = 'PASS'
    notes = []
    if skeleton:
        status = 'SKELETON'
        notes.append('skeleton-placeholder')
    if not name:
        notes.append('missing-name')
    if not description:
        notes.append('missing-description')
    if not all(sections.values()):
        missing = [k for k,v in sections.items() if not v]
        notes.append('missing-sections-' + '-'.join(missing).lower())
        status = 'FAIL'
    if status != 'SKELETON' and len(notes) == 0:
        status = 'PASS'
    return {
        'path': str(md_path),
        'name': name,
        'description': description,
        'status': status,
        'notes': notes,
        'sections': sections
    }

def main():
    results = []
    for md in ROOT.rglob('SKILL.md'):
        if md.is_file():
            results.append(scan_skill(md))
    report_path = ROOT / 'quality_report.md'
    with report_path.open('w', encoding='utf-8') as f:
        f.write('# Skills quality report\n\n')
        for r in sorted(results, key=lambda x: x['path']):
            f.write(f"- {r['path']} | status={r['status']} | name={r['name'] or 'N/A'}\n")
            f.write(f"  description: {r['description'] if r['description'] else 'N/A'}\n")
            f.write(f"  sections: {', '.join([s for s,ok in r['sections'].items() if ok]) or 'none'}\n")
            if r['notes']:
                f.write(f"  notes: {', '.join(r['notes'])}\n")
            f.write('\n')
    print(f'WROTE {report_path}')

if __name__ == '__main__':
    main()
