#!/usr/bin/env bash
# Public entrypoint: curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash -s -- --agent auto
set -euo pipefail
GHL_BOOTSTRAP="$(mktemp -d)"
trap 'rm -rf "$GHL_BOOTSTRAP"' EXIT
GHL_SOURCE='https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main'
curl --proto '=https' --tlsv1.2 -fsSL "$GHL_SOURCE/scripts/python-run.sh" -o "$GHL_BOOTSTRAP/python-run.sh"
curl --proto '=https' --tlsv1.2 -fsSL "$GHL_SOURCE/scripts/agent_setup.py" -o "$GHL_BOOTSTRAP/agent_setup.py"
bash "$GHL_BOOTSTRAP/python-run.sh" "$GHL_BOOTSTRAP/agent_setup.py" "$@"
