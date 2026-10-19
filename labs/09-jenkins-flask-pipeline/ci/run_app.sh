#!/usr/bin/env bash
# Start, stop or inspect the deployed app, tracking it with a PID file so it can
# always be stopped again.
# Usage: run_app.sh start|stop|status
# Environment: DEPLOY_ROOT (required), APP_PORT (default 5001),
#              APP_DIR (default $DEPLOY_ROOT/current),
#              APP_CMD (override the start command; default gunicorn from the release venv)
set -euo pipefail

: "${DEPLOY_ROOT:?DEPLOY_ROOT must be set}"
APP_PORT="${APP_PORT:-5001}"
APP_DIR="${APP_DIR:-$DEPLOY_ROOT/current}"
PID_FILE="$DEPLOY_ROOT/app.pid"
LOG_FILE="$DEPLOY_ROOT/app.log"

is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

case "${1:-}" in
  start)
    if is_running; then
      echo "error: already running (pid $(cat "$PID_FILE")); run stop first" >&2
      exit 1
    fi
    mkdir -p "$DEPLOY_ROOT"
    cd "$APP_DIR"
    cmd="${APP_CMD:-$APP_DIR/.venv/bin/gunicorn --bind 127.0.0.1:$APP_PORT app:app}"
    # shellcheck disable=SC2086  # the command is deliberately word-split
    $cmd > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 1
    if ! is_running; then
      echo "error: app exited immediately; log follows" >&2
      cat "$LOG_FILE" >&2 || true
      rm -f "$PID_FILE"
      exit 1
    fi
    echo "Started app (pid $(cat "$PID_FILE")) on port $APP_PORT"
    ;;
  stop)
    if [ ! -f "$PID_FILE" ]; then
      echo "Not running (no PID file)"
      exit 0
    fi
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      for _ in $(seq 1 20); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.5
      done
      kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "Stopped app (pid $pid)"
    ;;
  status)
    if is_running; then echo "running (pid $(cat "$PID_FILE"))"; else echo "not running"; exit 3; fi
    ;;
  *)
    echo "usage: $0 start|stop|status" >&2
    exit 2
    ;;
esac
