#!/usr/bin/env bash
# Apply and verify GitHub issue labels, project fields, dependencies, and parent.
#
# Usage:
#   issue_hygiene.sh --issue-url <url> --project <number> \
#     [--owner <org>] [--label <label>]... \
#     [--status <status>] [--priority <priority>] [--size <size>] \
#     [--blocked-by <issue-number-or-url>]... \
#     [--blocking <issue-number-or-url>]... \
#     [--parent <issue-number-or-url>]
#
# The script is additive and idempotent for labels and dependencies. It verifies
# every requested value after applying it and prints the issue URL on success.

set -euo pipefail

ISSUE_URL=""
PROJECT=""
OWNER="positron-ai"
PARENT=""
STATUS=""
PRIORITY=""
SIZE=""
LABELS=()
BLOCKED_BY=()
BLOCKING=()

usage() {
  sed -n '2,14p' "$0" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue-url) ISSUE_URL="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --owner) OWNER="$2"; shift 2 ;;
    --parent) PARENT="$2"; shift 2 ;;
    --status) STATUS="$2"; shift 2 ;;
    --priority) PRIORITY="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    --label) LABELS+=("$2"); shift 2 ;;
    --blocked-by) BLOCKED_BY+=("$2"); shift 2 ;;
    --blocking) BLOCKING+=("$2"); shift 2 ;;
    -h|--help) usage ;;
    *) echo "unknown flag: $1" >&2; usage ;;
  esac
done

[[ -z "$ISSUE_URL" ]] && { echo "error: --issue-url is required" >&2; exit 2; }
[[ -z "$PROJECT" ]] && { echo "error: --project is required" >&2; exit 2; }
[[ "$ISSUE_URL" != https://github.com/*/*/issues/* ]] && {
  echo "error: --issue-url must be a GitHub issue URL" >&2
  exit 2
}
if [[ ${#BLOCKED_BY[@]} -gt 0 && "$STATUS" != "Blocked" ]]; then
  echo "error: --blocked-by requires --status Blocked" >&2
  exit 2
fi
command -v jq >/dev/null || { echo "error: jq is required" >&2; exit 1; }

ISSUE_REPO="$(sed -E 's#https://github.com/([^/]+/[^/]+)/issues/[0-9]+.*#\1#' <<<"$ISSUE_URL")"

resolve_issue_url() {
  local ref="$1"
  if [[ "$ref" == https://github.com/*/*/issues/* ]]; then
    printf '%s\n' "$ref"
    return
  fi
  gh issue view "$ref" --repo "$ISSUE_REPO" --json url --jq .url
}

for label in "${LABELS[@]}"; do
  gh issue edit "$ISSUE_URL" --add-label "$label" >/dev/null
done

for ref in "${BLOCKED_BY[@]}"; do
  dependency_url="$(resolve_issue_url "$ref")"
  if ! gh issue view "$ISSUE_URL" --json blockedBy |
    jq -e --arg url "$dependency_url" 'any(.blockedBy.nodes[]; .url == $url)' >/dev/null; then
    gh issue edit "$ISSUE_URL" --add-blocked-by "$dependency_url" >/dev/null
  fi
done

for ref in "${BLOCKING[@]}"; do
  dependent_url="$(resolve_issue_url "$ref")"
  if ! gh issue view "$ISSUE_URL" --json blocking |
    jq -e --arg url "$dependent_url" 'any(.blocking.nodes[]; .url == $url)' >/dev/null; then
    gh issue edit "$ISSUE_URL" --add-blocking "$dependent_url" >/dev/null
  fi
done

if [[ -n "$PARENT" ]]; then
  parent_url="$(resolve_issue_url "$PARENT")"
  current_parent="$(gh issue view "$ISSUE_URL" --json parent --jq '.parent.url // ""')"
  [[ "$current_parent" == "$parent_url" ]] ||
    gh issue edit "$ISSUE_URL" --parent "$parent_url" >/dev/null
fi

project_id="$(gh project view "$PROJECT" --owner "$OWNER" --format json --jq .id)"
items_json="$(gh project item-list "$PROJECT" --owner "$OWNER" --limit 1000 --format json)"
item_id="$(jq -r --arg url "$ISSUE_URL" 'first(.items[] | select(.content.url == $url) | .id) // empty' <<<"$items_json")"
if [[ -z "$item_id" ]]; then
  gh project item-add "$PROJECT" --owner "$OWNER" --url "$ISSUE_URL" >/dev/null
  items_json="$(gh project item-list "$PROJECT" --owner "$OWNER" --limit 1000 --format json)"
  item_id="$(jq -r --arg url "$ISSUE_URL" 'first(.items[] | select(.content.url == $url) | .id) // empty' <<<"$items_json")"
fi
[[ -n "$item_id" ]] || { echo "error: could not resolve project item for $ISSUE_URL" >&2; exit 1; }

fields_json="$(gh project field-list "$PROJECT" --owner "$OWNER" --format json)"

set_single_select() {
  local field_name="$1"
  local option_name="$2"
  [[ -z "$option_name" ]] && return

  local field_id option_id
  field_id="$(jq -r --arg name "$field_name" 'first(.fields[] | select(.name == $name) | .id) // empty' <<<"$fields_json")"
  option_id="$(jq -r --arg field "$field_name" --arg option "$option_name" \
    'first(.fields[] | select(.name == $field) | .options[] | select(.name == $option) | .id) // empty' \
    <<<"$fields_json")"
  [[ -n "$field_id" && -n "$option_id" ]] || {
    echo "error: project field option not found: $field_name=$option_name" >&2
    exit 1
  }

  gh project item-edit \
    --id "$item_id" \
    --project-id "$project_id" \
    --field-id "$field_id" \
    --single-select-option-id "$option_id" >/dev/null
}

set_single_select Status "$STATUS"
set_single_select Priority "$PRIORITY"
set_single_select Size "$SIZE"

issue_json="$(gh issue view "$ISSUE_URL" --json labels,parent,blockedBy,blocking)"
for label in "${LABELS[@]}"; do
  jq -e --arg label "$label" 'any(.labels[]; .name == $label)' <<<"$issue_json" >/dev/null || {
    echo "error: label did not resolve: $label" >&2
    exit 1
  }
done
for ref in "${BLOCKED_BY[@]}"; do
  dependency_url="$(resolve_issue_url "$ref")"
  jq -e --arg url "$dependency_url" 'any(.blockedBy.nodes[]; .url == $url)' <<<"$issue_json" >/dev/null || {
    echo "error: blocked-by dependency did not resolve: $dependency_url" >&2
    exit 1
  }
done
for ref in "${BLOCKING[@]}"; do
  dependent_url="$(resolve_issue_url "$ref")"
  jq -e --arg url "$dependent_url" 'any(.blocking.nodes[]; .url == $url)' <<<"$issue_json" >/dev/null || {
    echo "error: blocking dependency did not resolve: $dependent_url" >&2
    exit 1
  }
done
if [[ -n "$PARENT" ]]; then
  parent_url="$(resolve_issue_url "$PARENT")"
  jq -e --arg url "$parent_url" '.parent.url == $url' <<<"$issue_json" >/dev/null || {
    echo "error: parent did not resolve: $parent_url" >&2
    exit 1
  }
fi

items_json="$(gh project item-list "$PROJECT" --owner "$OWNER" --limit 1000 --format json)"
item_json="$(jq -c --arg url "$ISSUE_URL" 'first(.items[] | select(.content.url == $url))' <<<"$items_json")"
for pair in "status:$STATUS" "priority:$PRIORITY" "size:$SIZE"; do
  field="${pair%%:*}"
  expected="${pair#*:}"
  [[ -z "$expected" ]] && continue
  actual="$(jq -r --arg field "$field" '.[$field] // ""' <<<"$item_json")"
  [[ "$actual" == "$expected" ]] || {
    echo "error: project field did not resolve: $field=$expected (got $actual)" >&2
    exit 1
  }
done

echo "$ISSUE_URL"
