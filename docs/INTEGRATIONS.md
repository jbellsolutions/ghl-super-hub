# Integration strategy and scale

## Pick the supported surface

Use Private Integration Tokens for internal account work where the operation's
security scheme allows them. Read `ghl hub schema OPERATION` to see required scopes
and whether agency/sub-account access is supported. A PIT cannot acquire unpublished
endpoints. Agency and sub-account tokens are not interchangeable.

For distributed installations, Marketplace webhooks, custom workflow actions/triggers,
or endpoints requiring OAuth, register a Marketplace app. An app is a connector,
not a way to gain unrestricted backend access. Build the missing logic in your own
service and connect it through supported webhook actions, custom actions, or APIs.
Use the dashboard when the missing operation is native GHL authoring.

## OAuth service implementation plan (not shipped as a hosted service)

1. Register an app at the HighLevel Marketplace developer portal.
2. Select distribution, supported account type, required scopes, and exact callback URL.
3. Start authorization with a random, single-use state tied to the requesting tenant.
4. At the callback validate state and exchange the code server-side using `/oauth/token`.
5. Store access/refresh tokens encrypted, with expiry, agency/location identity and scopes.
6. Serialize refresh per installation. Atomically replace both tokens on rotation.
7. For agency installs, use the documented location-token exchange when required;
   never use one tenant's access token for another.
8. On 401 refresh once if expiry is the cause. On 403 inspect scopes/account type;
   repeating the request or generating a different PIT is not a scope bypass.
9. Support uninstall/revocation and purge credentials according to retention policy.

This package accepts an already valid access token. It does not run a callback server,
store OAuth refresh credentials, or renew tokens automatically. No client secret is
needed to use PIT-supported API operations.

## Webhook service implementation plan

Use the official webhook documentation in `knowledge/upstream/docs/` and inspect
current signature/key rotation guidance before implementing verification. Verify the
signature over the original raw payload bytes, timestamp and event identity; do not
parse and re-serialize before signature verification. Deduplicate on installation
and event ID. Persist to a durable queue before acknowledgement. Workers operate with
that installation's token and keep event ordering where business logic requires it.
Do not assume a workflow custom webhook uses the Marketplace signature format.

Orgo computers have no public inbound hostname by default. Host OAuth callbacks and
webhook receivers on a separate reachable service. Hermes can consume queued jobs or
poll outbound; the CLI/MCP process is not a durable queue or webhook receiver.

## Operational scale

- Partition jobs, credentials, browser profiles, state and audit records by tenant.
- Use the API for bulk work. Reserve a browser session for authoring and exceptions.
- Persist each job's desired resource and returned IDs. Read before creating; names
  alone are not unique. Keep a deduplication key in the job store.
- Paginate using the operation's actual response cursor/offset contract. This CLI
  intentionally returns one page; it never invents a universal pagination loop.
- The supplied OAuth docs list burst/daily limits. Treat current response rate-limit
  headers and account limits as authoritative; throttle below the observed quota.
- GET/HEAD retry transient status codes at most three times. Mutations are never
  automatically retried. After a write timeout, reconcile with a read before retrying.
- Roll out templates to one test location, then a small cohort, then the rest. Track
  per-tenant completion and failures; do not run one uncontrolled browser fan-out.
- Use dashboard snapshots for supported configuration reuse. Check what a snapshot
  contains and what it overwrites before loading it; API snapshot listing/share/status
  is not a complete snapshot deployment interface.

See [official scopes](https://marketplace.gohighlevel.com/docs/Authorization/Scopes/)
and the pinned OAuth/webhook source documents. The bundle is an operator toolkit;
a fleet scheduler, OAuth broker, webhook receiver, queue and metrics service remain
separate engineering components if unattended multi-tenant operation is required.
