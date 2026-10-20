# Installation verification — 2026-10-20

## Implemented

- One-command bootstrap for existing Claude Code and/or Hermes installations.
- v2.3.1: Hermes compatibility setup via skills + MCP; no Hermes plugin-manager command.
- SHA-256 release verification before unpacking or registering the plugin.
- User-local isolated CLI/runtime; a managed Python fallback via uv when necessary.
- Claude Code marketplace/plugin manifests and an Agent Plugins v1 Hermes package.
- Runtime preparation and cached knowledge storage outside plugin caches.
- Hidden credential entry with mode 0600 storage outside the installed plugin.
- Portable symlink resolution without GNU-only `readlink -f`.

## Evidence

| Case | Result | Scope |
| --- | --- | --- |
| Protected existing 0600 credentials | Accepted by preflight without execute permission | Regression test for reported install failure |
| Orgo Hermes absent from PATH | `/opt/hermes/.venv/bin/hermes` discovered | Regression test |
| Hermes compatibility config | Actual PyYAML merge preserves unrelated settings; private backup; nine skills and six tools from configured stdio command | Isolated real configuration/MCP test; no agent process |
| Managed install repeat + collisions | Repeat succeeds; customized MCP and unowned skills preserved/reported | Automated tests |
| Full offline test suite | 52 passed | Source catalog, MCP, tenant isolation, installer, credentials and transport |
| Fresh installation into a temporary HOME with spaces | Passed | Real Python venv/pip, release extraction, CLI and MCP; native agent commands stubbed |
| v2.3 docs-only fresh + repeat | Passed | Real release extraction, venv/pip, CLI and MCP; native manager stubbed; no credentials created |
| Immediate repeat installation | Passed | Existing release reused; native registration repeated without destructive config edits |
| Python fallback | User-local uv acquired; usable Python 3.11.2 selected; shell profiles unchanged | Real fallback branch with unavailable Python candidates simulated |
| Fresh + repeat timing | 7.41 seconds together on this sandbox | Not a cross-platform performance guarantee |
| MCP through native runtime launcher | Six tools; valid JSON-only stdout | Real stdio process, prewarmed runtime |
| Cold native MCP startup | Six tools, JSON-only stdout, setup logs only on stderr, build snapshot isolated from plugin source | Real fresh runtime installation |
| Documentation search through installed CLI launcher | Passed | Real archived corpus/search |
| Wrong release checksum | Fails before native registration | Automated test |
| Traversal / symlink archive entries | Rejected | Automated test |
| Existing unrelated `ghl` executable | Preserved by installer | Installer code boundary; no overwrite flag |
| Missing prerequisites | JSON checklist before download; agent, Git, connection and writable paths checked | Automated tests |
| Interactive preflight with piped stdin | Real pseudo-terminal: hidden token entry or explicit docs-only choice; no release installation | Automated test with synthetic token |
| Missing Python without consent | Exit 2 checklist; no download in noninteractive mode | Automated test |
| Read-only preflight | Exit 0 when ready; no release download or installation | Automated test |
| Credentials | Hidden prompt, no token echo, mode 0600, newline injection refused | Automated tests with synthetic tokens only |
| Hermes portable manifest | Nine skills, one MCP server, zero diagnostics | Upstream `hermes_cli/agent_plugins.py` parser in an isolated harness |
| Skill frontmatter | All nine pass | Skill-creator quick validator |
| Setup-page render | Desktop render and no horizontal page overflow | Real Chromium via browser-harness |

The upstream parser harness supplied YAML parsing and inert declaration imports;
no Hermes agent or plugin-manager process was launched. No actual Claude Code
plugin-manager process was launched either. Hermes compatibility setup now writes
its documented skill/config surfaces directly and does not invoke a plugin manager. Native command argument shapes were
checked against current official docs/source and exercised with stub executables.

Linux/macOS GitHub Actions runs the offline suite and package builder. See the
repository's workflow results for actual runner status. A successful suite does
not prove GHL/Orgo credentials or hosted agent policies; live acceptance is separate.

## Remaining installation limits

Claude Code or Hermes must already be installed and usable, along with curl and
the native plugin manager's prerequisites (including Git). Native Windows uses WSL.
Internet restrictions, host permission/trust dialogs, old agent versions, Python
acquisition policy, and account authentication can still require user action.
A native-only first start may need a reconnect if setup exceeds a host's timeout.
The one-command path prewarms the runtime to reduce that work.

Orgo browser/computer provisioning and GHL authentication are not silently performed.
