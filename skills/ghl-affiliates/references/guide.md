# Affiliate campaigns

Status: documentation-derived; attribution and payouts require a target-account test.
Sources: [create campaign](https://help.gohighlevel.com/support/solutions/articles/155000003641-how-to-create-an-affiliate-campaign),
[prerequisites](https://help.gohighlevel.com/support/solutions/articles/155000003640-prerequisite-to-launch-your-first-affiliate-campaign),
[tracking](https://help.gohighlevel.com/support/solutions/articles/155000003643-how-to-track-leads-from-an-affiliate-campaign).

The imported public API reads affiliates, commissions and payouts. Search
`ghl hub operations --domain affiliate-manager` and inspect its location path and
pagination. Campaign creation, affiliate assignment/settings and payout execution
are dashboard work. Read-only payout access does not authorize paying anyone.

Inputs: source and landing page, eligible products or lead event, commission type
and rates, tier structure if requested, cookie duration, payout terms, affiliates
and desired draft/published state. Establish refund/commission rules explicitly.

1. Confirm the location; open Marketing → Affiliate Manager (or the current visible
   Affiliate Manager route). Open Campaigns, search for an existing campaign, or use
   `+ Add` to create one.
2. Select the campaign source and specific funnel/website/store or supported lead
   source. Choose the landing destination. Review the generated referral URL.
   Tracking applies source-wide, not just to the selected landing page.
3. For sales campaigns review the eligible product list. Set default percentage or
   fixed commission and product-level overrides if required. For lead campaigns
   configure the supported form/survey/calendar event rather than a sales product.
4. Configure advanced tiers only when requested. Check tier rates against margin and
   current platform limits; do not apply a multi-tier default to a simple program.
5. Enter the description, assign the intended affiliates, and set onboarding email,
   cookie duration, payout terms, setup-fee treatment and sub-affiliate settings.
6. Save as draft or publish according to the task. Reload and compare source,
   products, rates and assigned affiliates with the design.
7. Obtain a real test affiliate's generated campaign link. Open it in a clean browser
   context, complete an approved test conversion, and inspect attribution/commission.
   Confirm refund/adjustment handling separately if relevant. Do not incur real
   charges merely to test unless that cost is explicitly authorized.
8. Record campaign ID, source, link and evidence of the credited referral. Reconcile
   commission and payout reads through the public API where available.

Changing a campaign source generates a new referral URL and stops new attribution
on the old URL according to the source article. Record the impact before that change.
Notifying affiliates is an external message action and needs the user's instruction;
preparing an updated link alone is not permission to send it to others.
