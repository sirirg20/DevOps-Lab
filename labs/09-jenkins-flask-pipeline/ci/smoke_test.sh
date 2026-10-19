#!/usr/bin/env bash
# Check that a running instance serves the expected responses.
# Usage: smoke_test.sh <base-url>
# Environment: SMOKE_RETRIES (default 20), SMOKE_DELAY seconds (default 1),
#              EXPECTED_VERSION (optional; /version must report it)
set -euo pipefail

base="${1:?usage: smoke_test.sh <base-url>}"
retries="${SMOKE_RETRIES:-20}"
delay="${SMOKE_DELAY:-1}"
status=0

# check <description> <path> <expected substring, whitespace ignored>
check() {
  local desc=$1 path=$2 expected=$3 body=""
  for _ in $(seq 1 "$retries"); do
    body="$(curl -fsS --max-time 3 "$base$path" 2>/dev/null | tr -d ' \r\n' || true)"
    if [ -n "$body" ] && [[ "$body" == *"$expected"* ]]; then
      echo "PASS: $desc"
      return 0
    fi
    sleep "$delay"
  done
  echo "FAIL: $desc (GET $path, expected to contain '$expected', got '${body:-nothing}')" >&2
  status=1
}

check "root greets"        /        'HellofromtheFlaskpipeline!'
check "health reports ok"  /health  '"status":"ok"'
if [ -n "${EXPECTED_VERSION:-}" ]; then
  check "version is $EXPECTED_VERSION" /version "\"version\":\"$EXPECTED_VERSION\""
else
  check "version endpoint answers" /version '"version":'
fi

[ "$status" = 0 ] && echo "SMOKE TEST PASSED" || { echo "SMOKE TEST FAILED" >&2; exit 1; }
