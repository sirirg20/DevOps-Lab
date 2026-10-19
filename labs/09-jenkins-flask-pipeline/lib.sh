#!/usr/bin/env bash
# Shared helpers, sourced by create_job.sh and verify.sh.
# Loads .env and provides jenkins_get / jenkins_post that handle auth and the CSRF crumb.

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$LAB_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$LAB_DIR/.env"
  set +a
fi

JENKINS_PORT="${JENKINS_PORT:-8080}"
JENKINS_URL="http://localhost:${JENKINS_PORT}"
: "${JENKINS_ADMIN_USER:=admin}"
JOB_NAME=FlaskPipeline
CONTAINER=lab9-jenkins

COOKIE_JAR="$(mktemp)"
trap 'rm -f "$COOKIE_JAR"' EXIT

require_credentials() {
  [ -n "${JENKINS_ADMIN_PASSWORD:-}" ] || {
    echo "error: JENKINS_ADMIN_PASSWORD not set (create .env or run ./deploy.sh)" >&2
    exit 1
  }
}

wait_for_jenkins() {
  local code=000
  for _ in $(seq 1 60); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$JENKINS_URL/login" || true)"
    [ "$code" = 200 ] && return 0
    sleep 3
  done
  echo "error: Jenkins did not become ready (last status $code)" >&2
  return 1
}

# Prints "Header:value" for the CSRF crumb; the same session cookie must be sent with it.
crumb() {
  curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" -u "$JENKINS_ADMIN_USER:$JENKINS_ADMIN_PASSWORD" \
    "$JENKINS_URL/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,%22:%22,//crumb)"
}

jenkins_get() {
  curl -s -u "$JENKINS_ADMIN_USER:$JENKINS_ADMIN_PASSWORD" "$@"
}

# jenkins_post <curl args...>; prints the HTTP status code.
jenkins_post() {
  local token
  token="$(crumb)"
  curl -s -o /dev/null -w '%{http_code}' -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -u "$JENKINS_ADMIN_USER:$JENKINS_ADMIN_PASSWORD" -H "$token" -X POST "$@"
}
