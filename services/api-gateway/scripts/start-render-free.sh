#!/usr/bin/env bash
set -euo pipefail

AI_PORT="${AI_PORT:-8000}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-10000}"
export AI_SERVICE_URL="${AI_SERVICE_URL:-http://127.0.0.1:${AI_PORT}}"

cleanup() {
  if [[ -n "${AI_PID:-}" ]]; then
    kill "${AI_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

cd /app/services/ai-engine
python3 -m uvicorn app.main:app --host 127.0.0.1 --port "${AI_PORT}" &
AI_PID=$!

cd /app
node services/api-gateway/dist/index.js
