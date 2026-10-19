#!/usr/bin/env bash
# Print the pipeline job config.xml to stdout.
# Environment:
#   REPO_URL       git URL                       (default file:///repo-src)
#   BRANCH         branch spec                   (default */main)
#   SCRIPT_PATH    Jenkinsfile path in the repo  (default labs/09-jenkins-flask-pipeline/Jenkinsfile)
#   POLL_SCM_SPEC  cron spec to poll the repo    (default: none)
set -euo pipefail

cd "$(dirname "$0")"

# Escape &, <, > for XML text, then the characters that matter to the sed
# replacement below (backslash, ampersand, pipe).
xml_escape() { sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
sed_escape() { sed -e 's/[\\&|]/\\&/g'; }
esc() { printf '%s' "$1" | xml_escape | sed_escape; }

repo_url="$(esc "${REPO_URL:-file:///repo-src}")"
branch="$(esc "${BRANCH:-*/main}")"
script_path="$(esc "${SCRIPT_PATH:-labs/09-jenkins-flask-pipeline/Jenkinsfile}")"

if [ -n "${POLL_SCM_SPEC:-}" ]; then
  triggers="<triggers><hudson.triggers.SCMTrigger><spec>$(printf '%s' "$POLL_SCM_SPEC" | xml_escape)</spec><ignorePostCommitHooks>false</ignorePostCommitHooks></hudson.triggers.SCMTrigger></triggers>"
else
  triggers="<triggers/>"
fi

sed -e "s|@REPO_URL@|${repo_url}|" \
    -e "s|@BRANCH@|${branch}|" \
    -e "s|@SCRIPT_PATH@|${script_path}|" \
    -e "s|@TRIGGERS@|$(printf '%s' "$triggers" | sed_escape)|" \
    job/pipeline-config.xml.tmpl
