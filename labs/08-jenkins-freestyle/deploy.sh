#!/usr/bin/env bash
# Lab 8: create the sample repo, start Jenkins, and create the HelloWorld job.
set -euo pipefail

cd "$(dirname "$0")"

command -v docker >/dev/null 2>&1 || {
  echo "error: 'docker' not found on PATH (see docs/prerequisites.md)" >&2
  exit 1
}
docker compose version >/dev/null 2>&1 || {
  echo "error: the 'docker compose' plugin is required" >&2
  exit 1
}

if [ ! -f .env ]; then
  password="$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)"
  umask 077
  printf 'JENKINS_ADMIN_USER=admin\nJENKINS_ADMIN_PASSWORD=%s\n' "$password" > .env
  echo "==> Created .env (git-ignored) with a generated admin password"
fi

echo "==> Preparing the local sample repository"
./make_sample_repo.sh

echo "==> Building and starting Jenkins"
docker compose up -d --build

echo "==> Creating the job"
./create_job.sh

echo
echo "Open http://localhost:${JENKINS_PORT:-8080}/job/HelloWorld/ (credentials are in .env)"
echo "Click 'Build with Parameters', or run ./verify.sh to build and check automatically."
