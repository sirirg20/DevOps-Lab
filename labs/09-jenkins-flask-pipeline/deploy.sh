#!/usr/bin/env bash
# Lab 9: start Jenkins (with Python tooling) and create the FlaskPipeline job.
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

echo "==> Building and starting Jenkins"
docker compose up -d --build

echo "==> Creating the pipeline job"
./create_job.sh

echo
echo "Open http://localhost:${JENKINS_PORT:-8080}/job/FlaskPipeline/ (credentials are in .env)."
echo "The pipeline builds the last COMMITTED state of the repository, so commit first."
echo "Click 'Build Now', or run ./verify.sh to build and check automatically."
