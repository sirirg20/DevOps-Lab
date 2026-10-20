#!/usr/bin/env bash
# Tests for sample-code/hello-world.sh. Needs only bash.
set -uo pipefail

cd "$(dirname "$0")"
script=sample-code/hello-world.sh
failures=0

check() {
  local desc=$1 expected=$2 actual=$3
  if [ "$expected" = "$actual" ]; then
    echo "PASS: $desc"
  else
    echo "FAIL: $desc (expected '$expected', got '$actual')" >&2
    failures=$((failures + 1))
  fi
}

check "default greeting"      "Hello, Jenkins!" "$(env -u BUILD_NUMBER bash "$script")"
check "custom name"           "Hello, Asha!"    "$(env -u BUILD_NUMBER bash "$script" Asha)"
check "name with spaces"      "Hello, A B!"     "$(env -u BUILD_NUMBER bash "$script" "A B")"
check "exit status is zero"   "0"               "$(env -u BUILD_NUMBER bash "$script" >/dev/null; echo $?)"
check "no build info outside Jenkins" "1"       "$(env -u BUILD_NUMBER bash "$script" | wc -l | tr -d ' ')"
check "build info inside Jenkins" "job=demo build=#7" \
  "$(BUILD_NUMBER=7 JOB_NAME=demo bash "$script" | sed -n 2p)"

if [ "$failures" -eq 0 ]; then
  echo "ALL TESTS PASSED"
else
  echo "$failures TEST(S) FAILED" >&2
  exit 1
fi
