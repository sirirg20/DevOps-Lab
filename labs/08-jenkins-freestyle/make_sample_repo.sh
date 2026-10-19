#!/usr/bin/env bash
# Create a throwaway local git repository from sample-code/ for Jenkins to read.
# Usage: ./make_sample_repo.sh               create (or keep) the repo
#        ./make_sample_repo.sh --new-commit  add a commit, to demonstrate a rebuild
#
# The repo lives in .work/ (git-ignored). This script never pushes anywhere;
# publishing to GitHub is a manual step described in the README.
set -euo pipefail

cd "$(dirname "$0")"

REPO=.work/devops-sample-code

# Use the identity from your git config; fall back to a placeholder only for this throwaway repo.
git_id=()
if [ -z "$(git config user.name || true)" ] || [ -z "$(git config user.email || true)" ]; then
  git_id=(-c user.name="Lab 8" -c user.email="lab8@example.invalid")
fi

if [ ! -d "$REPO/.git" ]; then
  mkdir -p "$REPO"
  cp sample-code/hello-world.sh "$REPO/"
  chmod +x "$REPO/hello-world.sh"
  git -C "$REPO" init -q -b main
  git -C "$REPO" add hello-world.sh
  git -C "$REPO" "${git_id[@]}" commit -q -m "Add hello-world.sh"
  echo "Created $REPO with 1 commit on branch main"
fi

if [ "${1:-}" = "--new-commit" ]; then
  echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REPO/CHANGELOG.txt"
  git -C "$REPO" add CHANGELOG.txt
  git -C "$REPO" "${git_id[@]}" commit -q -m "Update changelog"
  echo "Added a commit; latest: $(git -C "$REPO" log --oneline -1)"
fi

git -C "$REPO" log --oneline
