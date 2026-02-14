#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"
PROFILE="${X_ARTICLES_PROFILE:-$HOME/.codex/browser-profiles/x-articles}"
URL="https://x.com/compose/articles"

if [[ $# -gt 0 && "$1" =~ ^https?:// ]]; then
  URL="$1"
  shift
fi

mkdir -p "$PROFILE"

exec "$PWCLI" open "$URL" --headed --persistent --profile "$PROFILE" "$@"
