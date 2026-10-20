# Funnels, landing pages and websites

Status: documentation-derived; no authenticated builder run has been completed.
Sources: [draft and publish](https://help.gohighlevel.com/support/solutions/articles/155000001913-save-draft-and-publish-funnels-and-websites),
[domains](https://help.gohighlevel.com/support/solutions/articles/48001153720-how-to-set-up-root-domain-subdomain-for-funnels-websites),
[form/checkout products](https://help.gohighlevel.com/support/solutions/articles/48001204219-how-to-create-and-add-products-to-a-funnel-website-payments-).

## API boundary and inputs

Use `ghl hub operations --domain funnels` for funnel/page listing, page counts and
redirect management. Page authoring is a visual-editor task. Media, products,
forms, surveys and payments have separate API domains with their own limitations.
Get the page objective, copy, assets, form/checkout/calendar destination, funnel
step order, domain/path, tracking requirements and requested publication state.

## Dashboard procedure

1. Confirm location and open Sites → Funnels or Websites. Search the existing assets.
   Open the intended funnel/site, or create it with the requested template/blank start.
2. Create/open the page/step. Set its name and URL path, then open the editor. Record
   whether edits affect an already published page and what the current publish flow is.
3. Build sections, rows, columns and elements. Apply the brand's fonts, colors, spacing,
   headings, images and button text. Upload assets to the target computer/media library.
4. Configure each CTA action, next-step link and anchor. Add the actual form, survey,
   calendar or order element. Verify selected resource IDs; a similarly named item may
   belong to a different campaign. For checkout select the intended products/prices.
5. Set SEO title/description, social image, favicon and relevant tracking settings.
   Use current help to place scripts in the proper location; avoid duplicate pixels.
6. Preview desktop and mobile. Inspect overflowing text, responsive ordering, hidden
   elements, images, form validation and clickable destinations. Save the draft and
   wait for the saved indicator; reopening must preserve the edited content.
7. Configure the custom domain and path in the actual domain settings. DNS changes
   require access to the domain provider; do not claim completion until verified.
   Check the domain's default page and redirect behavior before replacing them.
8. Publish if the user requested launch. Open the public URL in a separate browser
   context without the editor. Confirm HTTPS, the right content and every CTA.
9. Submit a controlled test lead or approved test checkout. Verify the resulting
   contact, form submission, order and workflow event in the intended location.
   A visual preview alone does not prove that the conversion path works.

Record funnel/site ID, page ID, URLs, live/draft state and test outcome. If the result
is uncertain, reopen/list assets rather than creating duplicates. Preserve the prior
version/duplicate page when the editor supports it. A code-rendered mockup is not a
native GHL page until imported or built and verified in the dashboard.
