#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKILL_DIR="$HERMES_HOME/skills/research/local-deep-research"

command -v uv >/dev/null 2>&1 || {
  echo "uv is required" >&2
  exit 1
}

uv tool install --editable "$ROOT" --force
mkdir -p "$(dirname "$SKILL_DIR")"
rm -rf "$SKILL_DIR"
ln -s "$ROOT/skills/local-deep-research" "$SKILL_DIR"

echo "Installed research-agent CLI and Hermes skill."
echo "Start a new Hermes session, then ask for private or open deep research."
