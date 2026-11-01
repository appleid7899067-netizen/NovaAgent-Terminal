#!/data/data/com.termux/files/usr/bin/bash
# Wrapper for installing skills with duplicate guard and logging

SKILL_NAME="$1"
IS_UPDATE=false
if [ "$2" == "--update" ]; then
    IS_UPDATE=true
fi

if [ -z "$SKILL_NAME" ]; then
    echo "Usage: $0 <skill-name> [--update]"
    exit 1
fi

BASE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
GUARD_SCRIPT="$BASE_DIR/skills/guard_duplicate_install.py"
LOG_DIR="$BASE_DIR/skills/guard_logs"
BACKUP_DIR="$BASE_DIR/skills/guard_backups"

mkdir -p "$LOG_DIR" "$BACKUP_DIR"

TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/guard_out_${SKILL_NAME}_${TS}.log"

echo "🔍 Checking for duplicate skill: $SKILL_NAME" | tee -a "$LOG_FILE"

# Run guard
python3 "$GUARD_SCRIPT" "$SKILL_NAME" 2>&1 | tee -a "$LOG_FILE"
GUARD_STATUS=${PIPESTATUS[0]}

if [ "$GUARD_STATUS" -ne 0 ]; then
    if [ "$IS_UPDATE" = true ]; then
        echo "🔄 Update mode: Backing up existing skill and proceeding..." | tee -a "$LOG_FILE"
        # Backup existing skill
        if [ -d "$BASE_DIR/skills/$SKILL_NAME" ]; then
            cp -r "$BASE_DIR/skills/$SKILL_NAME" "$BACKUP_DIR/${SKILL_NAME}_${TS}"
            echo "✅ Backup created: $BACKUP_DIR/${SKILL_NAME}_${TS}" | tee -a "$LOG_FILE"
        fi
    else
        echo "❌ Duplicate found. Aborting. Use --update to force." | tee -a "$LOG_FILE"
        exit 1
    fi
else
    echo "✅ No duplicate found. Proceeding..." | tee -a "$LOG_FILE"
fi

# ... existing install logic ...
echo "📦 Installing skill: $SKILL_NAME" | tee -a "$LOG_FILE"
# (Insert actual copy/creation logic here)
echo "✅ Installation complete." | tee -a "$LOG_FILE"
