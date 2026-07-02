#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd -P)"

cd "${ROOT}"

targets=(
  ".DS_Store"
  ".playwright-cli"
  "x_article_runs"
)

while IFS= read -r path; do
  targets+=("${path}")
done < <(find . -maxdepth 1 -type d -name 'tmp_*_publish' -print | sed 's#^\./##')

while IFS= read -r path; do
  targets+=("${path}")
done < <(find . -type d -name '__pycache__' -print | sed 's#^\./##')

removed=0
for target in "${targets[@]}"; do
  if [ -e "${target}" ]; then
    printf 'Removing %s\n' "${target}"
    rm -rf "${target}"
    removed=$((removed + 1))
  fi
done

if [ "${removed}" -eq 0 ]; then
  printf 'No local artifacts found.\n'
else
  printf 'Removed %s local artifact(s).\n' "${removed}"
fi
