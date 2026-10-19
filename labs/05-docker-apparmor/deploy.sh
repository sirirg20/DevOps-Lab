#!/usr/bin/env bash
# Lab 5: load the AppArmor profile and run the SDK scripts.
# Linux with AppArmor only. Does not install packages; it tells you what is missing.
set -euo pipefail

cd "$(dirname "$0")"

fail() { echo "error: $*" >&2; exit 1; }

[ "$(uname -s)" = "Linux" ] || fail "AppArmor needs a Linux kernel (use a Linux host, VM or WSL 2 with AppArmor)"
command -v docker >/dev/null 2>&1 || fail "docker not found"
command -v apparmor_parser >/dev/null 2>&1 || fail "apparmor_parser not found (Debian/Ubuntu package: apparmor)"
[ "$(cat /sys/module/apparmor/parameters/enabled 2>/dev/null || echo N)" = "Y" ] \
  || fail "AppArmor is not enabled in the running kernel"
python3 -c "import docker" 2>/dev/null \
  || fail "Python 'docker' package missing: pip install -r requirements-sdk.txt (in a venv)"

echo "==> Syntax-checking the profile"
sudo apparmor_parser -Q -K profile/lab5-restricted

echo "==> Loading the profile"
sudo apparmor_parser -r profile/lab5-restricted
sudo aa-status 2>/dev/null | grep -q lab5-restricted \
  && echo "profile lab5-restricted is loaded" \
  || echo "note: aa-status unavailable or profile not listed; the SDK check below is authoritative"

echo "==> Applying the profile to a container"
python3 apply_profile.py

echo "==> Comparing confined vs unconfined behaviour"
python3 check_restrictions.py
