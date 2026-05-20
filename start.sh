#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-8080}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"
export BACKEND_API_URL="${BACKEND_API_URL:-http://127.0.0.1:${BACKEND_PORT}}"
export HOSTNAME="${HOSTNAME:-0.0.0.0}"

echo "Starting ChilliGuard (nginx :${PORT}, backend :${BACKEND_PORT}, frontend :${FRONTEND_PORT})"

# ── Start backend ────────────────────────────────────────────────────────────
uvicorn main:app --app-dir /app/backend --host 0.0.0.0 --port "${BACKEND_PORT}" &
backend_pid=$!

# ── Start frontend ───────────────────────────────────────────────────────────
cd /app/frontend
PORT="${FRONTEND_PORT}" HOSTNAME=0.0.0.0 node server.js &
frontend_pid=$!

# ── Wait for backend to be ready (max 60s) ──────────────────────────────────
echo "[start.sh] Waiting for backend on :${BACKEND_PORT}..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/health" > /dev/null 2>&1; then
    echo "[start.sh] Backend is ready (${i}s)"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "[start.sh] WARNING: Backend did not become ready in 60s — starting nginx anyway"
  fi
  sleep 1
done

# ── Wait for frontend to be ready (max 60s) ──────────────────────────────────
echo "[start.sh] Waiting for frontend on :${FRONTEND_PORT}..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:${FRONTEND_PORT}/" > /dev/null 2>&1; then
    echo "[start.sh] Frontend is ready (${i}s)"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "[start.sh] WARNING: Frontend did not become ready in 60s — starting nginx anyway"
  fi
  sleep 1
done

# ── Start nginx AFTER both services are up ───────────────────────────────────
nginx -g 'daemon off;' &
nginx_pid=$!

trap 'kill ${backend_pid} ${frontend_pid} ${nginx_pid} 2>/dev/null || true' EXIT
wait -n "${backend_pid}" "${frontend_pid}" "${nginx_pid}"
