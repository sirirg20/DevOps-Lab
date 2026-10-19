#!/usr/bin/env bash
# Deploy a release tarball into <deploy-root>/releases/<version> and switch the
# "current" link to it, keeping only the newest N releases.
# Usage: deploy.sh <tarball> <deploy-root> [keep=3]
# Set SKIP_VENV=1 to skip creating the runtime virtualenv (used by the tests).
set -euo pipefail

tarball="${1:?usage: deploy.sh <tarball> <deploy-root> [keep]}"
root="${2:?usage: deploy.sh <tarball> <deploy-root> [keep]}"
keep="${3:-3}"

case "$keep" in
  ''|*[!0-9]*) echo "error: keep must be a positive number" >&2; exit 2 ;;
esac
[ "$keep" -ge 1 ] || { echo "error: keep must be at least 1" >&2; exit 2; }
[ -f "$tarball" ] || { echo "error: $tarball not found" >&2; exit 1; }

name="$(basename "$tarball" .tar.gz)"
version="${name#flask-app-}"
release="$root/releases/$version"

mkdir -p "$root/releases"
rm -rf "$release"
mkdir -p "$release"
# Read through stdin: GNU tar would read a "C:/..." archive path as host:file.
tar -xzf - -C "$release" < "$tarball"
[ -f "$release/app.py" ] || { echo "error: package has no app.py" >&2; exit 1; }

if [ "${SKIP_VENV:-0}" != "1" ]; then
  python3 -m venv "$release/.venv"
  "$release/.venv/bin/pip" install --quiet --no-cache-dir -r "$release/requirements.txt"
fi

# Build the new link beside the old one, then swap it into place in one step,
# so there is no moment when "current" is missing.
rm -rf "$root/current.new"
ln -sfn "$release" "$root/current.new"
if [ -L "$root/current.new" ]; then
  mv -Tf "$root/current.new" "$root/current"
else
  # No symlink support (for example Git Bash on Windows): ln made a plain copy.
  # Fall back to replacing the directory; not atomic, but the result is the same.
  rm -rf "$root/current"
  mv "$root/current.new" "$root/current"
fi
echo "Deployed version $version -> $root/current"

# Prune: keep the newest $keep releases and never remove the active one.
active="$(cat "$root/current/VERSION")"
ls -1 "$root/releases" | sort -n | head -n "-$keep" | while read -r old; do
  if [ "$old" != "$active" ]; then
    rm -rf "${root:?}/releases/$old"
    echo "Pruned release $old"
  fi
done
