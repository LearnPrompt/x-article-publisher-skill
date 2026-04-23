#!/usr/bin/env bash
set -euo pipefail

REPO="LearnPrompt/x-article-publisher-skill"
REF="${REF:-main}"
SKILL_NAME="x-article-publisher"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TARGET_DIR="${CODEX_HOME}/skills/${SKILL_NAME}"
INSTALL_DEPS="${INSTALL_DEPS:-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd -P || pwd)"

log() { printf '%s\n' "$*"; }
warn() { printf 'Warning: %s\n' "$*" >&2; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: $1 is required." >&2
    exit 1
  fi
}

require_cmd curl
require_cmd tar

LOCAL_SOURCE_DIR="${SCRIPT_DIR}/skills/${SKILL_NAME}"
if [ -f "${LOCAL_SOURCE_DIR}/SKILL.md" ]; then
  SOURCE_DIR="${LOCAL_SOURCE_DIR}"
  log "Installing from local checkout: ${SCRIPT_DIR}"
else
  TMP_DIR="$(mktemp -d)"
  cleanup() {
    rm -rf "${TMP_DIR}"
  }
  trap cleanup EXIT

  ARCHIVE_URL="https://codeload.github.com/${REPO}/tar.gz/refs/heads/${REF}"
  log "Downloading ${REPO}@${REF} ..."
  curl -fsSL "${ARCHIVE_URL}" | tar -xzf - -C "${TMP_DIR}"

  SOURCE_DIR="$(find "${TMP_DIR}" -type d -path "*/skills/${SKILL_NAME}" | head -n 1)"
  if [ -z "${SOURCE_DIR}" ] || [ ! -d "${SOURCE_DIR}" ]; then
    echo "Error: unable to locate skill directory in downloaded archive."
    exit 1
  fi
fi

mkdir -p "${CODEX_HOME}/skills"
rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

chmod +x "${TARGET_DIR}/scripts/"*.sh "${TARGET_DIR}/scripts/"*.py 2>/dev/null || true

install_python_deps() {
  if ! command -v python3 >/dev/null 2>&1; then
    warn "python3 is not installed. Install Python 3.9+ before publishing."
    return
  fi

  local req="${TARGET_DIR}/requirements.txt"
  if [ -f "${req}" ]; then
    log "Installing Python dependencies ..."
    python3 -m pip install --user -r "${req}"
  fi
}

install_playwright_cli() {
  if command -v playwright-cli >/dev/null 2>&1; then
    return
  fi
  if ! command -v npx >/dev/null 2>&1; then
    warn "npx is not installed. Install Node.js/npm for Playwright browser automation."
    return
  fi

  log "Priming Playwright MCP CLI ..."
  npx --yes --package @playwright/mcp playwright-cli --version >/dev/null 2>&1 || \
    warn "Unable to prime @playwright/mcp. It can still be installed on first use."
}

install_feishu2md() {
  if command -v feishu2md >/dev/null 2>&1; then
    return
  fi
  if command -v brew >/dev/null 2>&1; then
    log "Installing feishu2md with Homebrew ..."
    brew install feishu2md || warn "brew install feishu2md failed. Install it manually from https://github.com/Wsine/feishu2md/releases"
    return
  fi

  warn "feishu2md is not installed. Install it with Homebrew or from https://github.com/Wsine/feishu2md/releases for Feishu URL mode."
}

if [ "${INSTALL_DEPS}" != "0" ]; then
  install_python_deps
  install_playwright_cli
  install_feishu2md
else
  log "Skipping dependency installation because INSTALL_DEPS=0."
fi

log "Installed ${SKILL_NAME} to ${TARGET_DIR}"
log "Run environment check:"
log "  bash ${TARGET_DIR}/scripts/doctor.sh"
log "Done."
