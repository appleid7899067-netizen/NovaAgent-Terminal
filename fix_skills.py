import json

with open('skills/skills_config.json', 'r') as f:
    config = json.load(f)

new_skills = {
    'codex-engineer': 'Master-level software engineering workflow for complex coding tasks.',
    'short-video-creator': 'Creates short AI-generated video clips using Puter.js.',
    'ui-ux-designer': 'Enforces premium UI/UX design standards for any frontend task.',
    'browser-research': 'Automates web research tasks by combining browser navigation and summarization.',
    'code-assistant': 'A specialized skill for reading, writing, and refactoring code files.'
}

for name, desc in new_skills.items():
    config[name] = {
        'name': name,
        'description': desc,
        'source': 'custom',
        'enabled': True,
        'category': 'skill'
    }

with open('skills/skills_config.json', 'w') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)

print(f'✅ แก้ไขไฟล์สำเร็จ! ตอนนี้มีทั้งหมด {len(config)} Skill')
