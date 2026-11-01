#!/data/data/com.termux/files/usr/bin/bash

set -Eeuo pipefail

BROWSER="${BROWSER:-chromium-browser}"
CDP_HOST="${CDP_HOST:-127.0.0.1}"
CDP_PORT="${CDP_PORT:-9222}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-30}"

BASE_DIR="${TMPDIR:-/data/data/com.termux/files/usr/tmp}"
RUN_ID="chromium-$$-$(date +%s)"

PROFILE_DIR="${BASE_DIR}/${RUN_ID}-profile"
LOG_FILE="${BASE_DIR}/${RUN_ID}.log"

BROWSER_PID=""

cleanup() {
  local exit_code=$?

  # If startup failed before Chromium was launched, do not claim it was stopped.
  if [ -z "${BROWSER_PID}" ]; then
    exit "${exit_code}"
  fi

  echo
  echo "[browser] stopping Chromium..."

  if kill -0 "${BROWSER_PID}" 2>/dev/null; then
    kill "${BROWSER_PID}" 2>/dev/null || true

    for _ in $(seq 1 20); do
      if ! kill -0 "${BROWSER_PID}" 2>/dev/null; then
        break
      fi
      sleep 0.1
    done

    if kill -0 "${BROWSER_PID}" 2>/dev/null; then
      kill -KILL "${BROWSER_PID}" 2>/dev/null || true
    fi
  fi

  rm -rf "${PROFILE_DIR}" 2>/dev/null || true

  echo "[browser] Chromium stopped"
  echo "[browser] log: ${LOG_FILE}"

  exit "${exit_code}"
}

trap cleanup EXIT INT TERM

if ! command -v "${BROWSER}" >/dev/null 2>&1; then
  echo "[browser] ไม่พบคำสั่ง ${BROWSER}"
  echo "[browser] ตรวจสอบด้วย: which chromium-browser"
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "[project] ไม่ได้ระบุคำสั่งโปรเจกต์"
  echo "ตัวอย่าง:"
  echo "  ./scripts/with-chromium.sh npm run start"
  exit 1
fi

# Never attach to or interfere with an existing Browser/CDP instance.
if curl -fsS --max-time 1 \
  "http://${CDP_HOST}:${CDP_PORT}/json/version" \
  >/dev/null 2>&1; then
  echo "[browser] CDP ${CDP_HOST}:${CDP_PORT} ถูกใช้งานอยู่แล้ว"
  echo "[browser] ยกเลิกเพื่อไม่รบกวน Chromium ตัวอื่น"
  exit 1
fi

mkdir -p "${PROFILE_DIR}"

echo "[browser] starting ${BROWSER}"
echo "[browser] CDP: http://${CDP_HOST}:${CDP_PORT}"

"${BROWSER}" \
  --headless=new \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-software-rasterizer \
  --remote-debugging-address="${CDP_HOST}" \
  --remote-debugging-port="${CDP_PORT}" \
  --remote-allow-origins="http://${CDP_HOST}:${CDP_PORT}" \
  --user-data-dir="${PROFILE_DIR}" \
  about:blank \
  >"${LOG_FILE}" 2>&1 &

BROWSER_PID=$!

echo "[browser] PID: ${BROWSER_PID}"
echo "[browser] waiting for CDP..."

READY=0

for _ in $(seq 1 "${STARTUP_TIMEOUT}"); do
  if curl -fsS \
    --max-time 1 \
    "http://${CDP_HOST}:${CDP_PORT}/json/version" \
    >/dev/null 2>&1; then
    READY=1
    break
  fi

  if ! kill -0 "${BROWSER_PID}" 2>/dev/null; then
    echo "[browser] Chromium stopped unexpectedly"
    echo "[browser] log:"
    cat "${LOG_FILE}" 2>/dev/null || true
    exit 1
  fi

  sleep 1
done

if [ "${READY}" -ne 1 ]; then
  echo "[browser] CDP ไม่พร้อมภายใน ${STARTUP_TIMEOUT} วินาที"
  echo "[browser] log:"
  cat "${LOG_FILE}" 2>/dev/null || true
  exit 1
fi

echo "[browser] CDP ready"
echo "[project] running: $*"
echo

"$@"
