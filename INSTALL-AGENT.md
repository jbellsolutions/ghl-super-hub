# Install HighLevel Super Hub for me

I want you to install the HighLevel Super Hub plugin from
https://github.com/jbellsolutions/ghl-super-hub for the agent I am using.

## Do this

1. Identify whether this session uses Claude Code or Hermes. Run the corresponding
   command below in the same user account and environment as that agent:

   ```bash
   # Claude Code
   curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash -s -- --agent claude

   # Hermes
   curl -fsSL https://raw.githubusercontent.com/jbellsolutions/ghl-super-hub/main/install-agent.sh | bash -s -- --agent hermes
   ```

2. The installer verifies the release checksum, installs an isolated CLI/runtime,
   registers the plugin with the agent's native manager, and checks all six MCP tools.
   Let it complete. Keep existing unrelated settings and agent permission controls.
   If it fails, report the actual error; do not disable trust or overwrite another plugin.
3. Follow the installer's reported CLI path and use `hub doctor`. Check native plugin
   discovery when available. Namespaces vary: discover the installed ghl-operator
   skill rather than assuming its exact fully qualified name.
4. Tell me whether a new agent session/reconnect is needed to load the plugin. Do not
   launch a second agent session yourself just to test installation.
5. If credentials are absent, tell me to run `~/.local/bin/ghl hub connect` in an
   interactive terminal (or the printed absolute CLI path). It hides the token and
   saves it outside the plugin. Do not ask me to paste a token into chat. Use the
   environment's secure secret-entry tool instead if one is available and appropriate.
6. Once loaded, use the operator skill and the local knowledge tools. If GHL access is
   configured, verify the intended location with a read before any mutation.

## Boundaries

Installing the plugin does not authorize sending campaigns, charging payments,
creating paid Orgo computers, or changing live GHL records. Respect my actual task.
Browser automation still needs an existing computer/browser connection and a GHL
login; use the setup guide for Orgo. Never bypass MFA or browser challenges.

The one-command installer supports macOS and Linux, including Orgo and WSL. It
requires an already installed Claude Code or Hermes CLI, Git, curl, and internet access.
It finds a usable Python or downloads a user-local uv-managed Python without sudo
or shell-profile edits. Native Windows users should use WSL for this installer.
This installer cannot bypass host permission prompts, organizational policies,
network restrictions, or account authentication.
