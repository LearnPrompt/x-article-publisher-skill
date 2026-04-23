#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
STATUS=0

ok() { printf '[OK] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
fail() { printf '[FAIL] %s\n' "$*"; STATUS=1; }

case "${MODE}" in
  all|feishu|local) ;;
  *)
    echo "Usage: $0 [all|feishu|local]" >&2
    exit 2
    ;;
esac

if command -v python3 >/dev/null 2>&1; then
  PY_VERSION="$(python3 - <<'PY'
import sys
print(".".join(map(str, sys.version_info[:3])))
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
)" && ok "Python ${PY_VERSION}" || fail "Python 3.9+ is required"
else
  fail "python3 is required"
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 - <<'PY' >/dev/null 2>&1
from PIL import Image
PY
  then
    ok "Pillow installed"
  else
    fail "Pillow missing: python3 -m pip install --user Pillow"
  fi

  case "$(uname -s 2>/dev/null || echo unknown)" in
    Darwin)
      if python3 - <<'PY' >/dev/null 2>&1
from AppKit import NSPasteboard
from Foundation import NSData
PY
      then
        ok "macOS clipboard dependencies installed"
      else
        fail "macOS clipboard deps missing: python3 -m pip install --user pyobjc-framework-Cocoa"
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*)
      if python3 - <<'PY' >/dev/null 2>&1
import win32clipboard
from clipboard import Clipboard
PY
      then
        ok "Windows clipboard dependencies installed"
      else
        fail "Windows clipboard deps missing: python3 -m pip install --user pywin32 clip-util"
      fi
      ;;
    *)
      warn "Clipboard image paste is only implemented for macOS and Windows"
      ;;
  esac
fi

if command -v npx >/dev/null 2>&1; then
  ok "npx available"
else
  fail "npx is required for Playwright MCP fallback"
fi

if command -v playwright-cli >/dev/null 2>&1; then
  ok "playwright-cli available"
elif command -v npx >/dev/null 2>&1; then
  ok "playwright-cli can run via npx @playwright/mcp"
else
  fail "playwright-cli unavailable"
fi

if [ "${MODE}" = "all" ] || [ "${MODE}" = "feishu" ]; then
  if command -v feishu2md >/dev/null 2>&1; then
    ok "feishu2md available"
  else
    fail "feishu2md missing. macOS/Linux with Homebrew: brew install feishu2md"
  fi

  if [ -n "${FEISHU_APP_ID:-}" ] && [ -n "${FEISHU_APP_SECRET:-}" ]; then
    ok "Feishu credentials available from environment"
  elif [ -f "$HOME/Library/Application Support/feishu2md/config.json" ] || \
       [ -f "$HOME/.config/feishu2md/config.json" ] || \
       { [ -n "${APPDATA:-}" ] && [ -f "$APPDATA/feishu2md/config.json" ]; }; then
    ok "Feishu credentials config file found"
  else
    fail "Feishu credentials not found. Run: feishu2md config --appId <id> --appSecret <secret>"
  fi
fi

PROFILE="${X_ARTICLES_PROFILE:-$HOME/.codex/browser-profiles/x-articles}"
ok "X persistent profile path: ${PROFILE}"

exit "${STATUS}"
