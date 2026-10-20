# Orgo computer execution

Status: general procedure plus domain runbooks derived from official documentation.
No selectors, coordinates, or authenticated dashboard flows have been live-verified
in this package. Capture evidence when validating them on the target account.

1. Discover the configured Orgo MCP tools. Confirm the computer ID, status and workspace.
   Use an existing running computer; provision one only if that is part of the task.
2. Take a screenshot. Open the browser and the GHL application (including the account's
   white-label domain when applicable). Complete interactive login/MFA with the account
   holder if needed. Do not bypass challenges or extract browser refresh tokens.
3. Confirm the selected sub-account using its name and location ID in the URL/account
   controls. A login alone does not select the intended location.
4. Search the local help corpus for the task, then read its article. In the UI follow
   visible labels and current state. White-label menus, permissions, and UI releases
   can change the route; do not rely on stale coordinates or guessed selectors.
5. If available, use accessibility/DOM roles and labels for browser actions. For visual
   builders use screenshots and computer clicks. With coordinate tools take a fresh
   screenshot after navigation or layout changes. Do not reuse old screen coordinates.
6. Execute one meaningful action, wait for the visible result, and inspect it before
   proceeding. For file uploads use the computer's actual filesystem and file picker
   or supported upload tooling. A local shell path on another machine is not an upload.
7. Save and wait for the actual saved indicator. Reload/reopen the resource and compare
   values. Capture the resource URL/ID and its draft/published/scheduled state.
8. Perform the specialist's end-to-end test using a controlled test identity. Record
   observed evidence, not just clicks. Leave the final state requested by the user.

Recovery: If an action appears to stall, screenshot/read state before retrying.
Search by resource name and verify its ID before creating another. For a partially
completed resource resume it. If a save/publish/send outcome is uncertain, inspect
history/status first. A missing menu can indicate a role or plan limitation; stop
that dependent step and report the exact observed obstacle. Do not switch to an
unrelated account to make the menu appear.

Use one browser profile per tenant/operator identity. Scale data work through APIs,
not thousands of simultaneous browser tabs. Test a reusable snapshot once before
rolling it into additional sub-accounts.

Source: https://docs.orgo.ai/guides/mcp and https://docs.orgo.ai/guides/hermes.
