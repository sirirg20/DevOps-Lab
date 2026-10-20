#!/usr/bin/env bash
# Sample program the Freestyle job checks out and runs.
# Usage: ./hello-world.sh [name]     (name defaults to "Jenkins")
set -euo pipefail

name="${1:-Jenkins}"

echo "Hello, ${name}!"

# Jenkins exports these for every build; they are empty when run by hand.
if [ -n "${BUILD_NUMBER:-}" ]; then
  echo "job=${JOB_NAME:-unknown} build=#${BUILD_NUMBER}"
fi
