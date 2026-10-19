#!/usr/bin/env bash
# Lab 6: run a Jenkins controller that can drive the host's Docker.
# Usage: ./jenkins.sh start | stop
# Linux or WSL recommended; on Git Bash the socket mount depends on Docker Desktop.
set -euo pipefail

cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1   # stop Git Bash rewriting /var/run/... paths

NAME=lab6-jenkins
IMAGE=lab6-jenkins:1.0
VOLUME=lab6_jenkins_home

case "${1:-}" in
  start)
    command -v docker >/dev/null 2>&1 || { echo "error: docker not found" >&2; exit 1; }
    REPO_ROOT="$(git rev-parse --show-toplevel)"
    DOCKER_GID="$(stat -c '%g' /var/run/docker.sock 2>/dev/null || echo 0)"

    docker build -t "$IMAGE" jenkins
    docker volume create "$VOLUME" >/dev/null
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    docker run -d --name "$NAME" \
      -p 8080:8080 \
      -v "$VOLUME":/var/jenkins_home \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "$REPO_ROOT":/repo-src:ro \
      --group-add "$DOCKER_GID" \
      "$IMAGE"

    # Local repo mounted read-only so the job can use file:///repo-src before you push.
    docker exec "$NAME" git config --global --add safe.directory /repo-src/.git || true

    cat <<MSG
Jenkins is starting on http://localhost:8080
Initial admin password (printed by the command below, not stored anywhere):
  docker exec $NAME cat /var/jenkins_home/secrets/initialAdminPassword
Then follow the README section "Create the Jenkins job".
MSG
    ;;
  stop)
    docker rm -f "$NAME" >/dev/null 2>&1 || true
    echo "Stopped $NAME (volume $VOLUME kept; remove with ./cleanup.sh --jenkins)"
    ;;
  *)
    echo "usage: $0 start|stop" >&2
    exit 2
    ;;
esac
