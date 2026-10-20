# Build status — updated 2026-10-20

## One-command installation (v2.3.0)

Native Claude Code and Hermes plugin packages, a single-command release installer,
managed Python fallback, persistent sidecar runtimes, and hidden credential setup
are included. Preflight collects missing prerequisites before installation and asks
for secure GHL connection setup or an explicit documentation-only choice. A drop-in INSTALL-AGENT.md provides the same flow to either agent.
See [installation evidence](evals/2026-10-20-installation.md) for tested cases and limits.

## Shipped in this checkout

- Installed and runnable CLI with broad, source-generated API discovery/execution.
- 1,203 source-backed operation entries: 576 original-version + 627 v3 variants.
- Public API source archive: 157 files at revision `0af86a4cbd48c66a4071c7e509d1079f9f10ed17`.
- 798 saved help articles; 2,130 of 2,928 discovered article URLs remain missing.
- Full-text retrieval over help and official API source documents.
- Six-tool stdio MCP server and nine portable Hermes-compatible skills.
- Domain-specific dashboard procedures, integration/scale design and acceptance plan.
- Isolated tenant profiles, removal of hard-coded location fallbacks, inert dotenv
  parsing, fixed API origin, redirect refusal, bounded read retries, and no write replay.
- Portable archive builder that excludes secrets, environments, user attachments,
  personalized upstream builders, old skill instructions and sample live-account exports.

## Validation performed

`python -m unittest discover -s tests -v`: **45 tests passed**. Checks include source
catalog consistency, tenant isolation, no implicit location, no-network dry runs,
required body validation, unsafe path rejection, retries, redirect refusal, empty
responses, multipart handle closure, public OAuth form transport, CLI location handling,
article extraction, inert dotenv, blocked-ingestion reporting, MCP initialization,
tool validation, notifications and subprocess stdio JSON framing.

A clean extraction of the portable bundle was installed in an isolated directory and
its full offline suite passed there as well. CLI execution works from outside the
checkout. Skill installation was exercised in a temporary destination.

All nine skills pass the skill-creator quick validator. The validator's PyYAML
requirement was installed only in a temporary tool environment, not added to this
project's dependencies. Runtime dependencies remain those of the original CLI.

## External blockers and unverified work

The help portal returned HTTP 429 and then a Cloudflare `cf-mitigated: challenge`
response. Ingestion stopped without indexing the challenge. Saved articles remain
available. The crawler is resumable, paced, bounded, and reports incomplete coverage.
It does not solve access challenges or substitute error pages for content.

No GHL integration token, authenticated account browser, Hermes runtime, or Orgo
computer was connected. No live GHL data was changed. API permissions, actual
endpoint behavior, dashboard steps and published customer journeys are unverified.

The original convenience commands and experimental internal API builders have not
received a complete endpoint-by-endpoint audit. Use the official catalog for new
work; internal workflow creation remains opt-in and outside the MCP server.

OAuth refresh/storage, a hosted webhook receiver, durable job queues and fleet
orchestration are documented design work. They are not completed infrastructure.
