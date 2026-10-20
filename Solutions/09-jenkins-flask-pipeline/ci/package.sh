#!/usr/bin/env bash
# Build a versioned release tarball containing only what runs in production.
# Usage: package.sh <version> [output-dir]      -> <output-dir>/flask-app-<version>.tar.gz
set -euo pipefail

version="${1:?usage: package.sh <version> [output-dir]}"
out="${2:-dist}"
src="$(cd "$(dirname "$0")/../app" && pwd)"

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

# Explicit file list: tests, dev requirements and virtualenvs never ship.
cp "$src/app.py" "$src/requirements.txt" "$stage/"
printf '%s\n' "$version" > "$stage/VERSION"

mkdir -p "$out"
# Write through stdout: GNU tar would read a "C:/..." output path as host:file.
tar -czf - -C "$stage" app.py requirements.txt VERSION > "$out/flask-app-$version.tar.gz"
echo "Packaged $out/flask-app-$version.tar.gz"
