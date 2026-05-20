#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-8080}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"
export BACKEND_API_URL="${BACKEND_API_URL:-http://127.0.0.1:${BACKEND_PORT}}"
export HOSTNAME="${HOSTNAME:-0.0.0.0}"

echo "Starting ChilliGuard (nginx :${PORT}, backend :${BACKEND_PORT}, frontend :${FRONTEND_PORT})"

uvicorn main:app --app-dir /app/backend --host 0.0.0.0 --port "${BACKEND_PORT}" &
backend_pid=$!

cd /app/frontend
PORT="${FRONTEND_PORT}" HOSTNAME=0.0.0.0 node server.js &
frontend_pid=$!

nginx -g 'daemon off;' &
nginx_pid=$!

trap 'kill ${backend_pid} ${frontend_pid} ${nginx_pid} 2>/dev/null || true' EXIT
wait -n "${backend_pid}" "${frontend_pid}" "${nginx_pid}"
