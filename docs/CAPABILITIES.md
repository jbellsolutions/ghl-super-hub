# Capability coverage and gaps

Coverage is based on pinned official OpenAPI specs, official help articles and local
offline tests. All browser procedures are documentation-derived and need target-account
verification. Unsupported API authoring is routed to the dashboard, not fabricated.
Versioned API operations retain their own headers and namespace (`v3/DOMAIN`).

| Requested capability | Public API surface found | Dashboard work | Procedure |
| --- | --- | --- | --- |
| Workflows | List; contact enrollment/removal via contacts | Create graph, triggers/actions, settings, publish/test | [workflow](../skills/ghl-workflows/references/guide.md) |
| Funnels | List funnels/pages, counts, redirect CRUD | Create/edit steps, visual content, conversion wiring | [sites](../skills/ghl-sites/references/guide.md) |
| Landing pages/websites | Related funnel/page reads, media/form/product APIs | Page editor, layout, domains, publishing | [sites](../skills/ghl-sites/references/guide.md) |
| Email campaigns | Template create/read/update/delete, scheduled-email reads; legacy campaigns listing | Broadcast assembly/audience/scheduling; workflow nurture authoring | [email](../skills/ghl-email/references/guide.md) |
| Affiliate campaigns | Affiliate/commission/payout reads | Campaign setup, affiliate assignment, commission rules, payout execution | [affiliates](../skills/ghl-affiliates/references/guide.md) |
| Membership groups | Related contacts and workflow enrollment | Community/group/channel creation, access, moderation | [memberships](../skills/ghl-memberships/references/guide.md) |
| Courses | Documented nested course importer | Normal curriculum authoring, offers, access/drip, learner QA | [courses](../skills/ghl-courses/references/guide.md) |
| CRM/data operations | Contacts, opportunities, calendars, conversations, fields, objects and more | Account-specific exceptions/settings not in API | [API](../skills/ghl-api/references/guide.md) |
| Other GHL products | Search the full [API inventory](API-INVENTORY.md), including v3 chat widget/ads | Search current help, then follow observable UI with browser procedure | [browser](../skills/ghl-browser/references/guide.md) |

## Tooling status

| Component | Implemented | Verification |
| --- | --- | --- |
| CLI / one-command installation | Verified release installer, native Claude Code/Hermes plugins | Clean-home + repeat install; plugin-manager commands stubbed; see installation evidence |
| API catalog | 1,203 versioned operation entries | Every entry checked against its source path/method |
| Generic API executor | JSON, URL-encoded forms, multipart, refs/basic validation | Offline transport/validation tests; no live endpoint sweep |
| MCP server | Stdio initialization, discovery, execution and retrieval | Protocol/subprocess tests; no actual Hermes session supplied |
| Hermes skills | Nine with self-contained references | Skill validator passes; installer exercised in temporary destination |
| Orgo connector | Official hosted/stdio MCP configuration guide | No computer/account connected here |
| Browser procedures | Task-specific steps, verification and recovery | Official-doc-derived; selectors and live flows unverified |
| Help archive | 798 of 2,928 indexed articles | Partial; host challenge halted remaining ingestion |
| API source archive | 157 source/license files at a pinned revision | Downloaded, parsed, full-text indexed |
| OAuth token service | Design only | No refresh storage/broker implemented |
| Webhook receiver | Design only | No public receiver/queue implemented |
| Fleet scheduler | Design only | No unattended multi-tenant runtime implemented |

## Limits of generic API execution

Basic validation is not a full OpenAPI implementation. Check oneOf/anyOf/discriminator,
formats, ranges, business rules, complex query serialization and response contracts
against the original schemas. Requests returns one response page. The executor does
not auto-discover all pages, verify all scopes, renew OAuth credentials or reconcile
uncertain writes. These require the operation's documented contract and task logic.

Legacy convenience commands were not individually audited against all current schemas.
The hub catalog is the preferred route for new automation. Inherited internal API and
account-specific builder examples are experimental provenance, not supported coverage.

## Work remaining to reach operational mastery

1. Complete the missing help archive when the source is accessible; ingest any needed
   media/transcripts separately with source attribution. Add retrieval quality checks
   based on actual operator tasks; articles outside the sitemap are not asserted complete.
2. Connect the chosen Orgo computer, GHL browser session and scoped test integration.
3. Run every row of ACCEPTANCE.md; turn observed dashboard journeys into verified
   automation with stable selectors and per-account capability records.
4. Add dedicated wrappers for frequent complex API operations after testing them.
5. Implement the OAuth/webhook/queue components only if the deployment needs them;
   choose host, storage, tenancy and operational owner before building a fleet service.
6. Re-run source updates and acceptance tests as GHL, Hermes and Orgo evolve.
