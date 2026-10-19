#!/usr/bin/env bash
# Print the Freestyle job config.xml to stdout.
# Environment:
#   REPO_URL       git URL to check out        (default file:///sample-repo)
#   BRANCH         branch spec                 (default */main)
#   POLL_SCM_SPEC  cron spec to poll the repo  (default: none, manual builds only)
set -euo pipefail

cd "$(dirname "$0")"

# Escape &, <, > for XML text, then escape the characters that matter to the
# sed replacement below (backslash, ampersand, pipe).
xml_escape() { sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
sed_escape() { sed -e 's/[\\&|]/\\&/g'; }

repo_url="$(printf '%s' "${REPO_URL:-file:///sample-repo}" | xml_escape | sed_escape)"
branch="$(printf '%s' "${BRANCH:-*/main}" | xml_escape | sed_escape)"

if [ -n "${POLL_SCM_SPEC:-}" ]; then
  spec="$(printf '%s' "$POLL_SCM_SPEC" | xml_escape | sed_escape)"
  triggers="<triggers><hudson.triggers.SCMTrigger><spec>${spec}</spec><ignorePostCommitHooks>false</ignorePostCommitHooks></hudson.triggers.SCMTrigger></triggers>"
else
  triggers="<triggers/>"
fi

sed -e "s|@REPO_URL@|${repo_url}|" \
    -e "s|@BRANCH@|${branch}|" \
    -e "s|@TRIGGERS@|$(printf '%s' "$triggers" | sed_escape)|" \
    job/hello-world-config.xml.tmpl
