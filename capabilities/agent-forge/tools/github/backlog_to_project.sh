#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  backlog_to_project.sh --owner OWNER --project NUMBER --input FILE [--dry-run]

Input format:
  - Title
    Optional body lines
  - [ ] Title with checkbox syntax
    Optional body lines

Creates GitHub Project draft items using gh project item-create.
Requires gh auth with project scope.
EOF
}

owner=""
project=""
input=""
dry_run="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)
      owner="${2:-}"
      shift 2
      ;;
    --project)
      project="${2:-}"
      shift 2
      ;;
    --input)
      input="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$owner" || -z "$project" || -z "$input" ]]; then
  usage >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required but was not found in PATH." >&2
  exit 1
fi

if [[ ! -f "$input" ]]; then
  echo "Input file not found: $input" >&2
  exit 1
fi

titles=()
bodies=()
current_title=""
current_body=""

flush_item() {
  if [[ -n "$current_title" ]]; then
    titles+=("$current_title")
    bodies+=("$current_body")
  fi
  current_title=""
  current_body=""
}

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" =~ ^[[:space:]]*[-*][[:space:]]+(\[[[:space:]xX]?\][[:space:]]*)?(.*)$ ]]; then
    flush_item
    current_title="${BASH_REMATCH[2]}"
    continue
  fi

  if [[ -n "$current_title" ]]; then
    if [[ -z "$line" ]]; then
      current_body+=$'\n'
    elif [[ "$line" =~ ^[[:space:]]+(.*)$ ]]; then
      current_body+="${BASH_REMATCH[1]}"$'\n'
    else
      current_body+="$line"$'\n'
    fi
  fi
done < "$input"

flush_item

if [[ ${#titles[@]} -eq 0 ]]; then
  echo "No backlog items found in $input" >&2
  exit 1
fi

for i in "${!titles[@]}"; do
  title="${titles[$i]}"
  body="${bodies[$i]}"
  body="${body%$'\n'}"

  if [[ -z "$body" ]]; then
    body="$title"
  fi

  if [[ "$dry_run" == "true" ]]; then
    printf 'gh project item-create %s --owner %q --title %q --body %q\n' "$project" "$owner" "$title" "$body"
    continue
  fi

  gh project item-create "$project" --owner "$owner" --title "$title" --body "$body" >/dev/null
  echo "Created draft item: $title"
done
