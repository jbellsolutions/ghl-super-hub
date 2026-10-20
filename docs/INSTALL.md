# Install for Claude Code or Hermes

## Recommended: one command

```bash
curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash
```

It detects the installed agent(s). To target one, append `-s -- --agent claude` or
`-s -- --agent hermes` to `bash`. Or drop [INSTALL-AGENT.md](../INSTALL-AGENT.md)
into the agent and ask it to follow the instructions.

The installer downloads the latest release and SHA-256 checksum, verifies the ZIP,
installs an isolated CLI/runtime, registers the native plugin, and checks the six MCP
tools. It uses user-local directories without sudo or shell-profile edits. Claude
Code or Hermes and its native plugin prerequisites (including Git) must already be installed. Supported: macOS, Linux, Orgo and WSL;
use WSL on native Windows. Network/organization/agent trust prompts still apply.

A new agent session or MCP reconnect may be required. Discover the namespaced
`ghl-operator` skill through your agent's skill listing.

### Connect your account once

```bash
~/.local/bin/ghl hub connect
```

The prompt hides the token. Credentials are stored with private permissions at
`~/.config/ghl-super-hub/credentials.env` (or under `XDG_CONFIG_HOME`) and stay
outside plugin caches/releases. The command does not contact GHL. Environment
variables and explicit `--env-file` tenant profiles still work. Existing checkout
`.env` files remain the default for manual source installs.

### Native plugin commands

If you prefer your agent's own installation UI:

Claude Code:

```text
/plugin marketplace add jbellsolutions/ghl-super-hub
/plugin install ghl-super-hub@ghl-super-hub
```

Hermes:

```bash
hermes plugins install jbellsolutions/ghl-super-hub --enable
```

Native-only installs automatically prepare their isolated runtime on first MCP use;
the one-command installer prewarms it to reduce startup work. Cold installation can
still exceed a host's startup timeout on a slow network; reconnect after preparation.
No token is needed for local documentation search or API discovery.

The plugin does not provision an Orgo computer or silently grant browser/account
access. Follow the Orgo connection section below when you need dashboard work.

## Manual source / advanced installation

The remaining sections document manual installation and explicit MCP/profile setup.


This is a portable checkout bundle, not an independently deployed agent service.
Hermes is the agent, Orgo is its computer, and this package provides GHL tools and knowledge.
No separate agent is required. Keep this directory in a persistent location on the Orgo computer.

## 1. Prepare the computer

Use Orgo's Hermes Agent template or an existing computer with Hermes installed.
Follow the [official Hermes-on-Orgo guide](https://docs.orgo.ai/guides/hermes).
The curated template supervises the gateway; custom installations need a supervisor.
Orgo does not use systemd. Do not assume a background terminal survives restarts.

Copy/extract this package onto that computer, then:

```bash
cd /absolute/path/to/GHL
bash install.sh --link
export PATH="$HOME/.local/bin:$PATH"
```

Python 3.10+ and venv support are required. On Debian/Ubuntu, a missing `ensurepip`
requires the system `python3-venv` package. Installation uses only the starting CLI's
existing Python dependencies. New hub features use the standard library and requests.
The editable installation expects this checkout to remain in place; this is not a
standalone wheel containing the knowledge corpus.

## 2. Create a scoped GHL integration

1. Sign into the intended HighLevel sub-account.
2. Open Settings → Private Integrations → Create New (labels may vary).
3. Give the integration a descriptive name and choose scopes for your tasks.
4. Store the token in a protected dotenv file, not in chat or a shell command history.
5. Set `GHL_API_KEY` and `GHL_LOCATION_ID`; use the actual sub-account ID from the dashboard.
6. Use separate files and processes for separate tenants. The default file is the checkout's `.env`.

```bash
chmod 600 .env
./ghl hub doctor
./ghl hub call workflows:get-workflow
# Read the prepared request, then execute the read:
./ghl hub call workflows:get-workflow --execute
```

The request builder fills `locationId` only where the official operation explicitly
has a path/query parameter. Required body fields are supplied explicitly. A configured
location does not prove that a token belongs to it; verify the location with a live read.
`doctor` never prints a token and does not test remote permissions. OAuth access tokens
also work in `GHL_API_KEY`; refresh rotation is not implemented by this package.
See [integration design](INTEGRATIONS.md) for multi-account OAuth and webhooks.

## 3. Install skills

```bash
.venv/bin/python scripts/install_skills.py --dry-run
.venv/bin/python scripts/install_skills.py
```

The destination defaults to `~/.hermes/skills/`. Use `--destination` for a profile
or another agent's skills directory. Existing skills are refused unless `--replace`
is supplied. The installer includes an absolute CLI locator in every installed skill.
Restart/reload Hermes skill discovery, then ask it to use `ghl-operator`.

## 4. Connect GHL MCP

Merge `config/hermes-mcp.yaml.example` into the existing Hermes config; replace
absolute paths. For one tenant, the GHL server command is:

```yaml
mcp_servers:
  ghl:
    command: "/absolute/path/to/GHL/ghl"
    args: ["--env-file", "/secure/location-a.env", "hub", "mcp"]
```

Available tools: operation search, schema reading, prepared/executed requests,
help search, help article reading, and configuration diagnostics. No internal API
commands or browser credentials are exposed by this server. The server uses local
stdio; do not expose its stdin/stdout via an unauthenticated network bridge.

## 5. Give Hermes computer/browser control

Use the [official Orgo MCP](https://docs.orgo.ai/guides/mcp) at `https://www.orgo.ai/mcp`
if your Hermes build supports its remote OAuth flow. Sign in and authorize the
workspace containing the computer. Discover the offered tools: they are generated
from Orgo's current API and vary with authorization. Do not hard-code guessed names.

If remote OAuth is unsupported, Orgo documents a stdio alternative:

```yaml
mcp_servers:
  orgo:
    command: "npx"
    args: ["-y", "orgo-mcp-server"]
    # Supply ORGO_API_KEY securely in the server environment.
```

This optional external connector needs Node/npm and the Orgo MCP package. It is
not installed by this bundle. Provide `ORGO_API_KEY` through your secret manager /
Hermes process environment; verify inheritance in your version rather than putting
secrets in a committed config. Restrict tasks to the intended computer ID.

Log into GHL inside that computer's browser and complete MFA yourself when required.
The agent needs screenshots, click, type, key, scroll, and file access for upload tasks.
Shell access alone is not a browser control connection. See the `ghl-browser` skill.
Do not copy Firebase session tokens as a substitute for a browser login.

## 6. Verify before real work

Run `docs/ACCEPTANCE.md` in a disposable sub-account. CLI/MCP tests run offline in
this checkout; no live GHL or Orgo connection was supplied during development.
Successful local tests do not establish dashboard or permission coverage.

Sources: [Hermes skills](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md),
[Hermes MCP](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md),
[private integrations](https://help.gohighlevel.com/support/solutions/articles/155000003054-private-integrations-everything-you-need-to-know).
