#!/usr/bin/env bash
set -euo pipefail

REPO="LearnPrompt/x-article-publisher-skill"
REF="${REF:-main}"
SKILL_NAME="x-article-publisher"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
TARGET_DIR="${CODEX_HOME}/skills/${SKILL_NAME}"

if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required."
  exit 1
fi

if ! command -v tar >/dev/null 2>&1; then
  echo "Error: tar is required."
  exit 1
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

ARCHIVE_URL="https://codeload.github.com/${REPO}/tar.gz/refs/heads/${REF}"
echo "Downloading ${REPO}@${REF} ..."
curl -fsSL "${ARCHIVE_URL}" | tar -xzf - -C "${TMP_DIR}"

SOURCE_DIR="$(find "${TMP_DIR}" -type d -path "*/skills/${SKILL_NAME}" | head -n 1)"
if [ -z "${SOURCE_DIR}" ] || [ ! -d "${SOURCE_DIR}" ]; then
  echo "Error: unable to locate skill directory in downloaded archive."
  exit 1
fi

mkdir -p "${CODEX_HOME}/skills"
rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"

echo "Installed ${SKILL_NAME} to ${TARGET_DIR}"
echo "Done."
