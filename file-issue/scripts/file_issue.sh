#!/usr/bin/env bash
# Create a GitHub issue and add it to a positron-ai org-level Project (v2).
#
# Usage:
#   file_issue.sh --repo <owner/repo> --project <project-number> \
#                 --title <title> --body-file <path> \
#                 [--label <label>]... [--assignee <user>]... \
#                 [--owner <project-owner>]
#
# Defaults: --owner positron-ai
#
# Prints the created issue URL on stdout. Exits non-zero if either step fails.

set -euo pipefail

REPO=""
PROJECT=""
TITLE=""
BODY_FILE=""
OWNER="positron-ai"
LABELS=()
ASSIGNEES=()

usage() {
  sed -n '2,12p' "$0" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --body-file) BODY_FILE="$2"; shift 2 ;;
    --owner) OWNER="$2"; shift 2 ;;
    --label) LABELS+=("$2"); shift 2 ;;
    --assignee) ASSIGNEES+=("$2"); shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown flag: $1" >&2; usage ;;
  esac
done

[[ -z "$REPO" ]] && { echo "error: --repo is required" >&2; exit 2; }
[[ -z "$PROJECT" ]] && { echo "error: --project is required" >&2; exit 2; }
[[ -z "$TITLE" ]] && { echo "error: --title is required" >&2; exit 2; }
[[ -z "$BODY_FILE" ]] && { echo "error: --body-file is required" >&2; exit 2; }
[[ ! -f "$BODY_FILE" ]] && { echo "error: body file not found: $BODY_FILE" >&2; exit 2; }

create_args=(--repo "$REPO" --title "$TITLE" --body-file "$BODY_FILE")
for l in "${LABELS[@]}"; do create_args+=(--label "$l"); done
for a in "${ASSIGNEES[@]}"; do create_args+=(--assignee "$a"); done

ISSUE_URL="$(gh issue create "${create_args[@]}")"

if [[ -z "$ISSUE_URL" || "$ISSUE_URL" != https://github.com/* ]]; then
  echo "error: gh issue create did not return a URL" >&2
  echo "got: $ISSUE_URL" >&2
  exit 1
fi

gh project item-add "$PROJECT" --owner "$OWNER" --url "$ISSUE_URL" >/dev/null

echo "$ISSUE_URL"
