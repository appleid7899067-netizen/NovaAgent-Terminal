import sys
import os
import time

SKILL_NAME = sys.argv[1] if len(sys.argv) > 1 else None
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
LOG_DIR = os.path.join(SKILLS_DIR, "guard_logs")

os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

if not SKILL_NAME:
    log("❌ Error: Skill name required.")
    sys.exit(1)

skill_path = os.path.join(SKILLS_DIR, SKILL_NAME)
if os.path.exists(skill_path):
    log(f"⚠️ Duplicate found: {SKILL_NAME}")
    sys.exit(1)
else:
    log(f"✅ OK: {SKILL_NAME} is unique.")
    sys.exit(0)
