# Sources and provenance

## Starting point

User-supplied archive `gohighlevel-cli-main-1--1792447052497-b07ft1.zip`, archive root
`leadgenjay-gohighlevel-cli-1473bf380388f30323baa34b45235b992a5dd366`.
Original author attribution is retained in setup.py. The original README remains
in the private source workspace; it is not included in the public distribution.
The supplied archive did not contain a root LICENSE; no new license is asserted
for inherited code or help-center content.

## Official API documentation

Repository: https://github.com/GoHighLevel/highlevel-api-docs
Pinned revision and imported file count: `knowledge/api-source.json`.
Imported paths: apps/**/*.json, common/**/*.json, docs/**/*.md, README.md and LICENSE.
Original relative paths are preserved so schema references can be inspected.
The upstream CC0 license is retained in `knowledge/upstream/LICENSE`.
Root and v3 API operation variants are indexed separately. The documentation source
is a snapshot, not a claim about enabled features or live contract correctness.

## Official help center

Discovery: https://help.gohighlevel.com/support/sitemap.xml
Robots: https://help.gohighlevel.com/robots.txt
Saved articles: `knowledge/articles/<id>.json` with source URL, retrieval time,
source HTML SHA-256, normalized title/body and parser version.
Early cached titles are derived from the source URL slug and explicitly marked
`title_source: sitemap-url-slug`. Full body text remains source-derived.
Only article content is indexed; menus and unrelated recommendations are removed.
Links and image references are retained, while binary media/transcripts are not copied.
`help-status.json` records the last attempt; `coverage.json` lists every missing URL.
No complete-help claim is made while missing URLs remain.

## Hermes and Orgo

- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md
- https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md
- https://docs.orgo.ai/llms.txt
- https://docs.orgo.ai/guides/hermes
- https://docs.orgo.ai/guides/mcp

These official setup guides were consulted during the build. They are linked rather
than represented as a pinned installation of either runtime. No Orgo MCP package,
Hermes model, paid computer or account resource was provisioned during this work.
