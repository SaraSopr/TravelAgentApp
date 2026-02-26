#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PY="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$BACKEND_PY" ]]; then
  echo "[error] Python venv not found at $BACKEND_PY"
  echo "Run: python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]"
  exit 1
fi

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

echo "[dev] Starting backend on http://127.0.0.1:8000"
"$BACKEND_PY" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >/tmp/travel-agent-backend.log 2>&1 &
BACKEND_PID=$!

sleep 2
if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
  echo "[error] Backend failed to start. Check /tmp/travel-agent-backend.log"
  exit 1
fi

echo "[dev] Backend started (PID $BACKEND_PID). Launching mobile..."
exec "$ROOT_DIR/scripts/mobile_start.sh"
