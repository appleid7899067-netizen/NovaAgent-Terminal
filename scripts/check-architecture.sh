#!/data/data/com.termux/files/usr/bin/bash
# Architecture Ratchet checker — ตาม AGENT.md §7
# ใช้: bash check-architecture.sh [project_dir]
# ไม่แก้ไฟล์ใด ๆ — read-only scan

DIR="${1:-$HOME/NovaAgent-Clean}"
WARN=500
HOT=800

[ -d "$DIR" ] || { echo "❌ ไม่พบโฟลเดอร์: $DIR"; exit 1; }
cd "$DIR" || exit 1

echo "🏗️  Architecture Ratchet Report"
echo "   โฟลเดอร์: $DIR"
echo "   เกณฑ์: ⚠️  $WARN+ · 🔴 $HOT+ (hotspot = ห้ามโตต่อ)"
echo

find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  -not -path "*/.test-env/*" -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -not -path "*/venv/*" -not -path "*/site-packages/*" -not -path "*/CSJS/*" \
  -not -path "*/dist/*" -not -path "*/build/*" \
  -exec sh -c 'n=$(wc -l < "$1"); [ "$n" -ge '"$WARN"' ] && printf "%d\t%s\n" "$n" "$1"' _ {} \; 2>/dev/null \
  | sort -rn | awk -v hot="$HOT" '
    {n=$1; f=$2; if(n>=hot){h++; printf "🔴 %6d  %s\n", n, f} else {w++; printf "⚠️  %6d  %s\n", n, f}}
    END{printf "\n---\nรวม: 🔴 hotspot %d ไฟล์ · ⚠️ เฝ้าระวัง %d ไฟล์\n", h, w}
  '
