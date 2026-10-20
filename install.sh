#!/usr/bin/env bash
# Install from this portable checkout. No extra runtime dependencies beyond the supplied CLI.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ required'"
# Re-run venv creation even if a previously interrupted installation left the directory.
"$PY" -m venv .venv
.venv/bin/python -m pip install -e . --quiet
chmod +x ghl
if [ ! -f .env ]; then
  (umask 077; cp .env.example .env)
fi
if [ "${1:-}" = "--link" ]; then
  mkdir -p "$HOME/.local/bin"
  if [ -e "$HOME/.local/bin/ghl" ] || [ -L "$HOME/.local/bin/ghl" ]; then
    if [ ! "$HOME/.local/bin/ghl" -ef "$PWD/ghl" ]; then
      echo "Existing ~/.local/bin/ghl belongs to another installation; leaving it unchanged." >&2
      exit 1
    fi
  else
    ln -s "$PWD/ghl" "$HOME/.local/bin/ghl"
  fi
fi
printf '%s\n' 'Installed. Configure .env, then run ./ghl hub doctor.' 'For a PATH command: bash install.sh --link (ensure ~/.local/bin is on PATH).' 'Install the portable skills with: .venv/bin/python scripts/install_skills.py' 'See docs/INSTALL.md for Hermes MCP and Orgo setup.'
