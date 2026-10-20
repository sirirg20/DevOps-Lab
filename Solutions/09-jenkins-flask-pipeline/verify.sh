#!/usr/bin/env bash
# Lab 9: run the pipeline once and check every stage and output.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
require_credentials

fail=0
pass() { echo "PASS: $*"; }
bad()  { echo "FAIL: $*" >&2; fail=1; }
flat() { tr -d ' \n\r'; }

wait_for_jenkins && pass "Jenkins is reachable" || { bad "Jenkins not reachable"; exit 1; }
code="$(jenkins_get -o /dev/null -w '%{http_code}' "$JENKINS_URL/job/$JOB_NAME/api/json")"
[ "$code" = 200 ] && pass "job $JOB_NAME exists" || { bad "job $JOB_NAME missing (run ./create_job.sh)"; exit 1; }

# Queue a build with default parameters (the first run also registers the Jenkinsfile's parameters).
next="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/api/json" | flat | sed -n 's/.*"nextBuildNumber":\([0-9]*\).*/\1/p')"
status="$(jenkins_post "$JENKINS_URL/job/$JOB_NAME/build")"
[ "$status" = 201 ] && pass "build #$next queued" || { bad "queueing build returned HTTP $status"; exit 1; }

# Wait up to ~10 minutes (the first build downloads Python packages).
result=""
for _ in $(seq 1 200); do
  info="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/$next/api/json" 2>/dev/null | flat || true)"
  if echo "$info" | grep -q '"building":false'; then
    result="$(echo "$info" | sed -n 's/.*"result":"\([A-Z]*\)".*/\1/p')"
    break
  fi
  sleep 3
done
[ "$result" = SUCCESS ] && pass "build #$next finished with SUCCESS" || bad "build #$next result: '${result:-timed out}'"

console="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/$next/consoleText" || true)"

# Every stage ran, in order.
last=0
for stage in Prepare Build Lint Test Package Deploy "Smoke test"; do
  line="$(echo "$console" | grep -n "\[Pipeline\] { ($stage)" | head -1 | cut -d: -f1 || true)"
  if [ -n "$line" ] && [ "$line" -gt "$last" ]; then
    pass "stage '$stage' ran"; last="$line"
  else
    bad "stage '$stage' missing or out of order"
  fi
done
echo "$console" | grep -q 'SMOKE TEST PASSED' && pass "smoke test passed" || bad "no 'SMOKE TEST PASSED' in console"

# Test results were published.
total="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/$next/testReport/api/json" | flat | sed -n 's/.*"totalCount":\([0-9]*\).*/\1/p')"
[ "${total:-0}" -gt 0 ] && pass "JUnit report published ($total tests)" || bad "no JUnit test results"

# Artifact archived: ask Jenkins for the recorded path instead of guessing it.
rel="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/$next/api/json?tree=artifacts%5BrelativePath%5D" \
  | flat | grep -o "\"relativePath\":\"[^\"]*flask-app-$next\.tar\.gz\"" | head -1 | cut -d'"' -f4 || true)"
if [ -n "$rel" ]; then
  art="$(jenkins_get -o /dev/null -w '%{http_code}' "$JENKINS_URL/job/$JOB_NAME/$next/artifact/$rel")"
  [ "$art" = 200 ] && pass "artifact $rel archived and downloadable" || bad "artifact $rel not downloadable (HTTP $art)"
else
  bad "no flask-app-$next.tar.gz in the build's artifacts"
fi

# Deployed, and the app was stopped afterwards. The commands run inside the container.
docker exec "$CONTAINER" sh -c "[ \"\$(cat /var/jenkins_home/deploy/flask-app/current/VERSION)\" = '$next' ]" \
  && pass "release $next is the active deployment" || bad "active release is not $next"
docker exec "$CONTAINER" sh -c '[ ! -f /var/jenkins_home/deploy/flask-app/app.pid ]' \
  && pass "no app process left running" || bad "app.pid still present"

[ "$fail" = 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED" >&2; exit 1; }
