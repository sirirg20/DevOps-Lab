#!/usr/bin/env bash
# Lab 4: create a user-defined bridge network and run web, db and cache on it.
set -euo pipefail

cd "$(dirname "$0")"

command -v docker >/dev/null 2>&1 || {
  echo "error: 'docker' not found on PATH (see docs/prerequisites.md)" >&2
  exit 1
}

NET=lab-bridge-net

if [ -f .env ]; then
  # shellcheck disable=SC1091
  . ./.env
fi
if [ -z "${MYSQL_ROOT_PASSWORD:-}" ]; then
  MYSQL_ROOT_PASSWORD="$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)"
  echo "==> No .env found; generated a throwaway MySQL root password for this run"
fi

echo "==> Creating network $NET"
docker network inspect "$NET" >/dev/null 2>&1 || docker network create --driver bridge "$NET"

echo "==> Building flask-api image"
docker build -t flask-api:1.0 .

echo "==> Starting containers (db, cache have no published ports)"
docker rm -f db cache web >/dev/null 2>&1 || true
docker run -d --name db    --network "$NET" -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" mysql:8.4
docker run -d --name cache --network "$NET" redis:7-alpine
docker run -d --name web   --network "$NET" -p 5001:5001 flask-api:1.0

echo "==> Containers started. MySQL needs ~20-30s to accept connections."
echo "    Run ./verify.sh to check name resolution and connectivity."
