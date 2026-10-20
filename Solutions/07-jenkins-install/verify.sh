#!/usr/bin/env bash
# Lab 7: verify the installation.
# Usage: ./verify.sh [manual|auto] [--persistence]
#   --persistence (auto only) recreates the container and checks data survived.
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:-auto}"
PERSIST="${2:-}"
PORT="${JENKINS_PORT:-8080}"
URL="http://localhost:$PORT"
fail=0

pass() { echo "PASS: $*"; }
bad()  { echo "FAIL: $*" >&2; fail=1; }

if [ "$MODE" = manual ]; then
  NAME=lab7-jenkins-manual
else
  NAME=lab7-jenkins
fi

# 1. Container is running and publishes the expected port.
if [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = true ]; then
  pass "container $NAME is running"
else
  bad "container $NAME is not running"
fi
docker port "$NAME" 8080/tcp 2>/dev/null | sed 's/^/      port mapping: /' || true

# 2. The web UI answers (wait while Jenkins starts).
code=000
for _ in $(seq 1 40); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$URL/login" || true)"
  [ "$code" = 200 ] && break
  sleep 3
done
[ "$code" = 200 ] && pass "GET /login returned 200" || bad "GET /login returned $code"

# 3. Version header proves it is Jenkins.
version="$(curl -sI "$URL/login" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-jenkins"{print $2}')"
[ -n "$version" ] && pass "X-Jenkins header present (version $version)" || bad "no X-Jenkins header"

if [ "$MODE" = auto ]; then
  # shellcheck disable=SC1091
  . ./.env
  # 4. Anonymous access is refused.
  anon="$(curl -s -o /dev/null -w '%{http_code}' "$URL/api/json" || true)"
  [ "$anon" = 403 ] || [ "$anon" = 401 ] \
    && pass "anonymous /api/json refused ($anon)" || bad "anonymous /api/json returned $anon (expected 401/403)"

  # 5. The admin account works.
  authed="$(curl -s -o /dev/null -w '%{http_code}' -u "$JENKINS_ADMIN_USER:$JENKINS_ADMIN_PASSWORD" "$URL/api/json" || true)"
  [ "$authed" = 200 ] && pass "admin login works via API" || bad "admin API call returned $authed"

  # 6. Preinstalled plugins are present.
  plugins="$(curl -s -u "$JENKINS_ADMIN_USER:$JENKINS_ADMIN_PASSWORD" "$URL/pluginManager/api/json?depth=1" || true)"
  for p in workflow-aggregator git credentials-binding; do
    echo "$plugins" | tr -d ' ' | grep -q "\"shortName\":\"$p\"" \
      && pass "plugin $p installed" || bad "plugin $p missing"
  done

  # 7. Optional: data survives removing and recreating the container.
  if [ "$PERSIST" = "--persistence" ]; then
    docker exec "$NAME" sh -c 'echo ok > /var/jenkins_home/.lab7-marker'
    docker compose down
    docker compose up -d
    for _ in $(seq 1 40); do
      [ "$(curl -s -o /dev/null -w '%{http_code}' "$URL/login" || true)" = 200 ] && break
      sleep 3
    done
    docker exec "$NAME" test -f /var/jenkins_home/.lab7-marker \
      && pass "data persisted across container re-creation" || bad "marker file lost: volume not persisting"
  fi
else
  echo "note: manual mode has no preconfigured credentials; check the plugin list and a test job in the UI."
fi

[ "$fail" = 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED" >&2; exit 1; }
