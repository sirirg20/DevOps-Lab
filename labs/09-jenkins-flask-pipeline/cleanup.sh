#!/usr/bin/env bash
# Lab 9: stop Jenkins. --all also deletes its data volume (including deployed
# releases and build history) and the image.
set -euo pipefail

cd "$(dirname "$0")"

# The compose file requires the password variable even for `down`.
JENKINS_ADMIN_PASSWORD="${JENKINS_ADMIN_PASSWORD:-unused}" docker compose down --remove-orphans >/dev/null 2>&1 || true

if [ "${1:-}" = "--all" ]; then
  docker volume rm lab9_jenkins_home >/dev/null 2>&1 || true
  docker rmi lab9-jenkins >/dev/null 2>&1 || true
  rm -rf .venv dist reports
  echo "Removed container, volume, image and local build output."
else
  echo "Stopped Jenkins. Data kept; use --all to delete the volume, image and build output."
fi
