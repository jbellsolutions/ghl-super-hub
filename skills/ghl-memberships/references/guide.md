# Communities and membership groups

Status: documentation-derived; roles and access paths have not been live-tested.
Sources: [community setup](https://help.gohighlevel.com/support/solutions/articles/155000000280-how-to-setup-customize-and-manage-your-communities),
[members](https://help.gohighlevel.com/support/solutions/articles/155000000289-communities-how-to-manage-members-inside-groups),
[group access workflow](https://help.gohighlevel.com/support/solutions/articles/155000001239-automate-community-group-access-with-workflows).

No community group CRUD operations are present in the imported public catalog.
Use the dashboard. A CRM contact is not automatically a member of every group;
a course offer does not necessarily grant community/private-channel access.

Inputs: community/group name and slug, branding/domain, privacy/join policy,
channels, roles/moderation, course availability and enrollment/removal rules.

1. Confirm the sub-account. Open its Memberships/Communities area; menu placement
   can also be within Client Portal/Sites depending on the current UI. Confirm the
   visible route with the current community setup article and screenshot.
2. Create/open the community and group. Set the name, URL slug and description.
   Save, record the group ID/URL, and check for any existing group with that slug.
3. In community settings configure branding: logo, cover, favicon and theme. Set
   custom domain only if requested and DNS access is available. Verify the portal
   URL before using it in invitations or checkout links.
4. Set the intended public/private visibility, joining/approval rules, member roles
   and moderation controls. Create channels and apply private-channel access where
   needed. A group-level member role and a channel-specific role may differ.
5. Add/pin initial content and link courses/learning content if in scope. Verify
   whether courses are free, paid, time-unlocked, level-unlocked or individually gated.
6. Inspect portal/community email preferences. The documented route may be Sites →
   Client Portal → Memberships → Settings → Email Settings → Communities. Review
   default sender settings and invitation/approval notifications before adding users.
7. Add a controlled test member or process a test join request. Complete login as
   that member. Verify intended channels/content and lack of access to restricted
   content. Administrator view is insufficient for this test.
8. For automatic access, configure documented workflow actions/triggers through the
   workflow builder. Test both grant and revoke paths with the same controlled identity.
9. Reopen settings and record the group URL/ID, privacy, membership result and any
   email notifications observed. Leave real invitations to the user's authorized task.

Recover by adjusting the particular membership/channel/course grant. Deleting a CRM
contact as a substitute for revoking group access can have wider consequences; inspect
the documented contact/group behavior first. Bulk member changes require a tenant-scoped
job record and read-back/reconciliation, even if executed through the browser.
