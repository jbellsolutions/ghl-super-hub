#!/usr/bin/env bash
# Public entrypoint: curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash -s -- --agent auto
set -euo pipefail
if ! command -v curl >/dev/null 2>&1; then
  printf '%s\n' 'Before installation: curl is needed. Install it with your operating system package manager, then rerun this command.' >&2
  exit 2
fi
export GHL_INSTALL_PREFLIGHT=1
GHL_BOOTSTRAP="$(mktemp -d)"
trap 'rm -rf "$GHL_BOOTSTRAP"' EXIT
GHL_SOURCE='https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main'
curl --proto '=https' --tlsv1.2 -fsSL "$GHL_SOURCE/scripts/python-run.sh" -o "$GHL_BOOTSTRAP/python-run.sh"
curl --proto '=https' --tlsv1.2 -fsSL "$GHL_SOURCE/scripts/agent_setup.py" -o "$GHL_BOOTSTRAP/agent_setup.py"
bash "$GHL_BOOTSTRAP/python-run.sh" "$GHL_BOOTSTRAP/agent_setup.py" "$@"
