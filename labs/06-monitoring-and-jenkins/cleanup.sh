#!/usr/bin/env bash
# Lab 6: remove the monitoring stack. --jenkins also removes the Jenkins
# container, its data volume and its image.
set -euo pipefail

cd "$(dirname "$0")"

# The compose file requires the variable to be set, even for `down`.
GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-unused}" docker compose down -v --rmi local --remove-orphans

if [ "${1:-}" = "--jenkins" ]; then
  docker rm -f lab6-jenkins >/dev/null 2>&1 || true
  docker volume rm lab6_jenkins_home >/dev/null 2>&1 || true
  docker rmi lab6-jenkins:1.0 >/dev/null 2>&1 || true
fi
echo "Cleaned up."
