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
