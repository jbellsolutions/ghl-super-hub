# Live acceptance checklist

Local test status is recorded in `docs/BUILD-STATUS.md`. These checks need actual GHL
and Orgo access and should use a disposable sub-account and controlled test identities.
Record observed resource IDs, timestamps, statuses and screenshots privately.

| Check | Pass evidence |
| --- | --- |
| Hermes discovery | All nine skill names appear; installed references point at the correct checkout |
| MCP handshake | Hermes lists six GHL tools; doctor/search work without a write |
| Orgo computer | Screenshot/click/type/key/scroll tools act on the intended computer |
| Tenant isolation | Separate profile processes resolve different location IDs; a missing token fails |
| Token scopes | Location read succeeds; requested domains tested independently; denied scopes fail clearly |
| Contacts | Create one controlled contact, read/update it, and verify the selected location |
| Workflow | Build draft, trigger test enrollment, inspect each branch/history, leave requested state |
| Funnel/page | Save draft, publish to test URL, inspect mobile/desktop, submit test form and verify contact |
| Email | Create template and draft campaign, send to test address, verify merge fields and unsubscribe |
| Affiliate | Create draft campaign and test affiliate journey; reconcile tracked conversion/commission |
| Community | Add test member, confirm intended private/public access and revoke it |
| Course | Build small draft curriculum, verify media and offer enrollment through learner login |
| Rate limiting | Observe real response headers and configure fleet quotas accordingly |
| Restart | Restart computer/gateway, confirm credentials, skill discovery and browser session behavior |

Do not mark a row passed based only on a CLI exit code or admin preview. Remove only
the test resources created for this verification, within the authorized test account.

Production fleet acceptance additionally needs a durable queue, OAuth refresh/revoke
coverage when applicable, webhook verification/replay tests, per-tenant throttling,
audit retention, reconciliation after uncertain writes, and a staged rollout. Those
services are design work described in INTEGRATIONS.md, not a shipped deployment.
