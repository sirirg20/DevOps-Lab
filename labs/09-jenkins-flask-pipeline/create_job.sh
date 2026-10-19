#!/usr/bin/env bash
# Create (or update) the FlaskPipeline job through the Jenkins REST API.
# Honors REPO_URL, BRANCH, SCRIPT_PATH and POLL_SCM_SPEC from the environment or .env.
set -euo pipefail

cd "$(dirname "$0")"
# shellcheck disable=SC1091
. ./lib.sh
require_credentials
wait_for_jenkins

xml="$(mktemp)"
trap 'rm -f "$xml" "$COOKIE_JAR"' EXIT
./render_job.sh > "$xml"

exists="$(jenkins_get -o /dev/null -w '%{http_code}' "$JENKINS_URL/job/$JOB_NAME/api/json")"
if [ "$exists" = 200 ]; then
  echo "==> Job $JOB_NAME exists; updating its configuration"
  status="$(jenkins_post -H 'Content-Type: application/xml' --data-binary "@$xml" \
    "$JENKINS_URL/job/$JOB_NAME/config.xml")"
else
  echo "==> Creating job $JOB_NAME"
  status="$(jenkins_post -H 'Content-Type: application/xml' --data-binary "@$xml" \
    "$JENKINS_URL/createItem?name=$JOB_NAME")"
fi

case "$status" in
  200|201) echo "OK: job $JOB_NAME configured (HTTP $status) -> $JENKINS_URL/job/$JOB_NAME/" ;;
  *) echo "error: Jenkins returned HTTP $status" >&2; exit 1 ;;
esac
