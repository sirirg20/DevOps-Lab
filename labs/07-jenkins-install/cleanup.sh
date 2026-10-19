#!/usr/bin/env bash
# Lab 7: stop and remove Jenkins. Data volumes are kept unless --volumes is given.
set -euo pipefail

cd "$(dirname "$0")"

# The compose file requires the password variable even for `down`.
JENKINS_ADMIN_PASSWORD="${JENKINS_ADMIN_PASSWORD:-unused}" docker compose down --remove-orphans >/dev/null 2>&1 || true
docker rm -f lab7-jenkins-manual >/dev/null 2>&1 || true

if [ "${1:-}" = "--volumes" ]; then
  docker volume rm lab7_jenkins_home lab7_manual_home >/dev/null 2>&1 || true
  docker rmi lab7-jenkins >/dev/null 2>&1 || true
  echo "Removed containers, volumes and image."
else
  echo "Removed containers. Data volumes kept; use --volumes to delete them."
fi
