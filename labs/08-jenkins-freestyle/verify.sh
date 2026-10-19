#!/usr/bin/env bash
# Lab 8: run a build of the HelloWorld job and check the outcome.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
require_credentials

fail=0
pass() { echo "PASS: $*"; }
bad()  { echo "FAIL: $*" >&2; fail=1; }
flat() { tr -d ' \n\r'; }

# 1. Jenkins up, job exists.
wait_for_jenkins && pass "Jenkins is reachable" || { bad "Jenkins not reachable"; exit 1; }
code="$(jenkins_get -o /dev/null -w '%{http_code}' "$JENKINS_URL/job/$JOB_NAME/api/json")"
[ "$code" = 200 ] && pass "job $JOB_NAME exists" || { bad "job $JOB_NAME missing (run ./create_job.sh)"; exit 1; }

# 2. Trigger a parameterized build and remember which build number it will get.
next="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/api/json" | flat | sed -n 's/.*"nextBuildNumber":\([0-9]*\).*/\1/p')"
status="$(jenkins_post "$JENKINS_URL/job/$JOB_NAME/buildWithParameters?GREETEE=Verifier")"
[ "$status" = 201 ] && pass "build #$next queued" || { bad "queueing build returned HTTP $status"; exit 1; }

# 3. Wait for it to finish.
result=""
for _ in $(seq 1 60); do
  info="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/$next/api/json" 2>/dev/null | flat || true)"
  if echo "$info" | grep -q '"building":false'; then
    result="$(echo "$info" | sed -n 's/.*"result":"\([A-Z]*\)".*/\1/p')"
    break
  fi
  sleep 3
done
[ "$result" = SUCCESS ] && pass "build #$next finished with SUCCESS" || bad "build #$next result: '${result:-timed out}'"

# 4. Console output proves the script from Git ran with the parameter.
console="$(jenkins_get "$JENKINS_URL/job/$JOB_NAME/$next/consoleText" || true)"
echo "$console" | grep -q 'Hello, Verifier!' && pass "console shows 'Hello, Verifier!'" || bad "greeting missing from console"
echo "$console" | grep -qiE 'Cloning|Fetching|Checking out' && pass "console shows the Git checkout" || bad "no Git checkout in console"

# 5. The file was fetched into the workspace.
docker exec lab8-jenkins test -f "/var/jenkins_home/workspace/$JOB_NAME/hello-world.sh" \
  && pass "hello-world.sh is in the job workspace" || bad "hello-world.sh not found in workspace"

echo "--- last lines of console output"
echo "$console" | tail -8

[ "$fail" = 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED" >&2; exit 1; }
