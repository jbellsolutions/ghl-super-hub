# Install HighLevel Super Hub for me

I want you to install the HighLevel Super Hub plugin from
https://github.com/jbellsolutions/ghl-super-hub for the agent I am using.

## Do this

1. Identify whether this session uses Claude Code or Hermes. Check for the selected
   CLI, Git, curl, a writable user directory and a usable Python 3.10+ with venv.
   For Hermes, also inspect `/opt/hermes/.venv/bin/hermes` before concluding it is
   missing. The installer discovers that location automatically; explicit overrides
   are `GHL_HERMES_BIN` and `GHL_HERMES_PYTHON`. Keep the agent’s active `HERMES_HOME`.
   Ask me for any missing prerequisite or needed approval **before** installing.
   Do not install an entire agent, use sudo, or download a runtime without approval.
2. Run the read-only checklist in the same user account/environment as the agent:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash -s -- --agent claude --preflight
   # Replace claude with hermes when this session uses Hermes.
   ```

   Exit code 2 means setup needs input, not a completed installation. Explain the
   checklist and ask for the missing choices first. If Python is missing, the
   bootstrap reports that first; get approval for managed runtime setup or help
   provide Python, then rerun preflight to collect the remaining requirements.
3. If credentials are missing, ask whether I want to connect GHL now or install
   documentation only. Use the environment's secure secret-entry tool to provide
   `GHL_API_KEY` and `GHL_LOCATION_ID`, or direct me to run the interactive command
   in my terminal for hidden token entry. If a protected tenant profile already
   exists, pass its path with `--credentials-file /secure/tenant.env` in both
   preflight and install. A 0600 file is correct; never make it executable.
   Never ask for a token in chat or pass one
   in a shell argument. Preserve existing tenant profiles. Documentation-only mode
   requires my explicit choice; do not silently skip the connection.
4. Once requirements are resolved, install with:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash -s -- --agent claude --non-interactive
   ```

   Substitute `hermes` as appropriate. Add `--docs-only` only if I chose that mode.
   An interactive terminal can omit `--non-interactive` and answer setup prompts.
   The installer verifies the release checksum, installs the isolated CLI/runtime,
   configures the agent, and verifies all eight MCP tools. Claude uses its native
   plugin; Hermes installs nine skills and merges MCP into its existing config
   with a private backup. This avoids requiring portable-plugin support. Hermes’s
   Python must already provide PyYAML. Do not retry the old Hermes plugin-manager
   route or force-replace a partial plugin installation. Respect host trust
   prompts. On an unexpected failure, report the actual cause without bypassing
   permissions or replacing unrelated settings.
5. Use the printed CLI path and `hub doctor`. Discover the installed `ghl-operator`
   skill; namespaces vary. Tell me whether a new session/reconnect is needed. Do
   not launch another agent session just to test installation. Report account
   configuration separately from live API access, which installation does not verify.
6. Before dashboard tasks, check for an existing Orgo/browser connection and GHL
   login; ask for missing access then. Browser provisioning is a separate setup
   step, not a prerequisite for local documentation/API tools. Before any GHL
   mutation, verify the intended location with an authorized read.

## Boundaries

Installing the plugin does not authorize sending campaigns, charging payments,
creating paid Orgo computers, or changing live GHL records. Respect my actual task.
Browser automation still needs an existing computer/browser connection and a GHL
login; use the setup guide for Orgo. Never bypass MFA or browser challenges.

The one-command installer supports macOS and Linux, including Orgo and WSL. It
requires an already installed Claude Code or Hermes CLI, Git, curl, and internet access.
It finds a usable Python or asks before downloading a user-local uv-managed Python without sudo
or shell-profile edits. Native Windows users should use WSL for this installer.
This installer cannot bypass host permission prompts, organizational policies,
network restrictions, or account authentication.
