#!/usr/bin/env bash
# Lab 7: install Jenkins with Docker.
# Usage: ./deploy.sh manual   stock image + interactive setup wizard
#        ./deploy.sh auto     custom image, plugins and admin user from files (default)
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:-auto}"
PORT="${JENKINS_PORT:-8080}"

command -v docker >/dev/null 2>&1 || {
  echo "error: 'docker' not found on PATH (see docs/prerequisites.md)" >&2
  exit 1
}

case "$MODE" in
  manual)
    echo "==> Starting stock Jenkins LTS (setup wizard mode) on 127.0.0.1:$PORT"
    docker volume create lab7_manual_home >/dev/null
    docker rm -f lab7-jenkins-manual >/dev/null 2>&1 || true
    docker run -d --name lab7-jenkins-manual \
      -p "127.0.0.1:$PORT:8080" \
      -v lab7_manual_home:/var/jenkins_home \
      jenkins/jenkins:lts-jdk17
    cat <<MSG

Jenkins is starting (about a minute). Then:
  1. Get the unlock password (shown only to you, not stored in this repo):
       docker exec lab7-jenkins-manual cat /var/jenkins_home/secrets/initialAdminPassword
  2. Open http://localhost:$PORT, paste the password, choose "Install suggested plugins",
     create your admin user, accept the instance URL.
  3. Run ./verify.sh manual
MSG
    ;;
  auto)
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
    echo "==> Building image (plugins are downloaded now) and starting Jenkins"
    docker compose up -d --build
    echo
    echo "Jenkins is starting on http://localhost:$PORT (log in with the credentials in .env)."
    echo "Run ./verify.sh auto to check it."
    ;;
  *)
    echo "usage: $0 manual|auto" >&2
    exit 2
    ;;
esac
