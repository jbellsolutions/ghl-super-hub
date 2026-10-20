# Course authoring and access

Status: documentation-derived; import and learner journeys need live acceptance tests.
Sources: [build courses](https://help.gohighlevel.com/support/solutions/articles/48001141015-how-to-build-courses-membership-sites),
[new course editor](https://help.gohighlevel.com/support/solutions/articles/155000007613-edit-membership-courses-with-the-new-course-editor),
[grant access](https://help.gohighlevel.com/support/solutions/articles/155000002845-how-to-grant-access-to-membership-courses-using-workflows).

## API boundary

`ghl hub schema courses:import-courses` documents the single public course importer.
It has a specific nested content schema; it is not a generic create/update lesson API.
Inspect required objects, supported media/content types and visibility enums before
preparing a payload. Use the browser for normal authoring and offer management.
The executor supports multipart file uploads through `--files`; inspect the specific
media API schema rather than sending file bytes to the course importer.

Inputs: learning objective, curriculum/categories/modules/lessons, media and downloads,
assessments, branding/domain, publication, drip/lock rules, offer pricing and access.

## Dashboard procedure

1. Confirm location and open Memberships → Courses/Products (follow the current visible
   Client Portal navigation if relocated). Search existing courses before creating one.
2. Create/open the course with the requested template. Set the title, description,
   image and structure. Treat the actual editor's module/category/lesson terminology
   as authoritative rather than assuming an older UI layout.
3. Add categories/modules and lessons in curriculum order. Configure titles, lesson
   text and media. Upload or select videos, audio, documents and thumbnails. Wait for
   processing to complete; an uploaded filename alone does not prove playable content.
4. Add assessments/assignments, completion criteria and certificates if requested.
   Set lesson visibility and drip/lock settings. Review current drip semantics so
   enrollment-relative timing is not confused with a fixed release date.
5. Save the course and preview as a learner. Check ordering, media playback, downloads,
   links, text formatting, completion and locked content. A builder preview may bypass
   access restrictions, so it is only one part of verification.
6. Create/open the offer that grants the course. Include the correct products/courses,
   price/free-access rules, checkout and access duration where available. A published
   course and a saleable offer are distinct resources. Test payment integrations only
   with an authorized test mode or approved test charge.
7. Configure grant/revoke offer workflow actions where required. Ensure trigger filters
   target the correct product/offer and preserve existing enrollment rules.
8. Use a controlled learner account to enroll through the actual free/purchase/access
   path. Verify portal login, intended course/lesson access, progress, notifications,
   drip behavior and revocation. Also test that an unentitled learner cannot access it.
9. Set publication state to the requested result. Reopen and record course ID, offer
   ID, portal/checkout URLs and test evidence. For community learning, verify the
   separate group/channel/course gating with the membership skill.

For imports, start with a small draft test course and verify the imported structure
before scaling. After an uncertain write, inspect the product list before retrying;
the importer is not documented as safely idempotent. Preserve the prior course/offer
and its existing students when making updates.
