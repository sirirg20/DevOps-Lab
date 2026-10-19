#!/usr/bin/env bash
# Lab 6: build and start the exporter, Prometheus and Grafana, then smoke-test.
set -euo pipefail

cd "$(dirname "$0")"

for tool in docker; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "error: '$tool' not found on PATH (see docs/prerequisites.md)" >&2
    exit 1
  }
done
docker compose version >/dev/null 2>&1 || {
  echo "error: the 'docker compose' plugin is required" >&2
  exit 1
}

if [ ! -f .env ]; then
  password="$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)"
  umask 077
  printf 'GRAFANA_ADMIN_PASSWORD=%s\n' "$password" > .env
  echo "==> Created .env (git-ignored) with a generated Grafana admin password"
fi

echo "==> Building and starting the stack"
docker compose up -d --build

echo "==> Smoke test"
./smoke_test.sh

cat <<'MSG'

Stack is up:
  Exporter    http://localhost:8000/metrics
  Prometheus  http://localhost:9090   (Status > Targets, Alerts)
  Grafana     http://localhost:3000   (user: admin, password: see .env)
  Dashboard   Delivery Overview (provisioned automatically)
MSG
