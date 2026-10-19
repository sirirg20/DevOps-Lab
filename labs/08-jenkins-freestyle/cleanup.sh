#!/usr/bin/env bash
# Lab 8: stop Jenkins. --all also deletes its data volume, image and the local sample repo.
set -euo pipefail

cd "$(dirname "$0")"

# The compose file requires the password variable even for `down`.
JENKINS_ADMIN_PASSWORD="${JENKINS_ADMIN_PASSWORD:-unused}" docker compose down --remove-orphans >/dev/null 2>&1 || true

if [ "${1:-}" = "--all" ]; then
  docker volume rm lab8_jenkins_home >/dev/null 2>&1 || true
  docker rmi lab8-jenkins >/dev/null 2>&1 || true
  rm -rf .work
  echo "Removed container, volume, image and local sample repo."
else
  echo "Stopped Jenkins. Data kept; use --all to delete the volume, image and sample repo."
fi
