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

if [[ -x "$PWCLI" ]]; then
  exec "$PWCLI" open "$URL" --headed --persistent --profile "$PROFILE" "$@"
fi

if command -v playwright-cli >/dev/null 2>&1; then
  exec playwright-cli open "$URL" --headed --persistent --profile "$PROFILE" "$@"
fi

if command -v npx >/dev/null 2>&1; then
  exec npx --yes --package @playwright/mcp playwright-cli open "$URL" --headed --persistent --profile "$PROFILE" "$@"
fi

echo "Error: Playwright CLI not found. Install Node.js/npm, then run: npx --yes --package @playwright/mcp playwright-cli install" >&2
exit 1
