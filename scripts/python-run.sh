#!/usr/bin/env bash
# Find a usable Python, or acquire a user-local uv-managed runtime. Never edit shell profiles.
set -euo pipefail
if [ -n "${GHL_PYTHON:-}" ]; then
  "$GHL_PYTHON" -c 'import sys, venv, ensurepip; assert sys.version_info >= (3,10)' >&2
  exec "$GHL_PYTHON" "$@"
fi
for candidate in python3 python3.14 python3.13 python3.12 python3.11 python3.10; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys, venv, ensurepip; assert sys.version_info >= (3,10)' >/dev/null 2>&1; then
    exec "$candidate" "$@"
  fi
done
# Installation must ask before acquiring a runtime. MCP startup remains noninteractive.
if [ "${GHL_INSTALL_PREFLIGHT:-0}" = 1 ]; then
  for option in "$@"; do
    case "$option" in
      --preflight|--non-interactive)
        printf '%s\n' '{"status":"needs_input","needs":[{"id":"python","action":"Install Python 3.10+ with venv/ensurepip, or rerun interactively to approve a user-local runtime download."}]}'
        exit 2 ;;
    esac
  done
  if ! { exec 3<>/dev/tty; } 2>/dev/null; then
    printf '%s\n' 'Before installation: Python 3.10+ with venv/ensurepip is needed. Rerun interactively to approve a user-local uv/Python download.' >&2
    exit 2
  fi
  printf '%s' 'Python is needed. Download user-local uv/Python (no sudo or profile edits)? [y/N]: ' >&3
  read -r answer <&3 || answer=n
  exec 3>&-
  case "$answer" in y|Y|yes|YES) ;; *) printf '%s\n' 'Setup paused; no runtime downloaded.' >&2; exit 2 ;; esac
fi
GHL_TOOLS="${XDG_DATA_HOME:-$HOME/.local/share}/ghl-super-hub/tools"
if command -v uv >/dev/null 2>&1; then
  GHL_UV="$(command -v uv)"
else
  GHL_UV="$GHL_TOOLS/uv"
  if [ ! -x "$GHL_UV" ]; then
    mkdir -p "$GHL_TOOLS"
    installer="$(mktemp)"
    trap 'rm -f "$installer"' EXIT
    curl --proto '=https' --tlsv1.2 -fsSL https://astral.sh/uv/install.sh -o "$installer"
    UV_UNMANAGED_INSTALL="$GHL_TOOLS" sh "$installer" >&2
    rm -f "$installer"
    trap - EXIT
  fi
fi
exec "$GHL_UV" run --no-project --python 3.11 python "$@"
