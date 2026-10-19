#!/usr/bin/env bash
# Lab 5: remove lab containers and image, and unload the profile.
set -euo pipefail

cd "$(dirname "$0")"

if command -v docker >/dev/null 2>&1; then
  docker ps -aq --filter "label=lab=05-docker-apparmor" | xargs -r docker rm -f
  docker rmi lab5-flask:1.0 >/dev/null 2>&1 || true
fi

if command -v apparmor_parser >/dev/null 2>&1 && [ "$(uname -s)" = "Linux" ]; then
  sudo apparmor_parser -R profile/lab5-restricted 2>/dev/null || true
fi
echo "Cleaned up."
