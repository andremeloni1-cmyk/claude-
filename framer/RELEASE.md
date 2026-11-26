# Framer release procedure

Status: staged for review on 26 November 2026; production approval not granted.

- Project: iuFAULj0ZU07WpAzPDbI; Blog collection: EEv3Nygkn.
- Review branch: ky3c2mftk (soft-shore).
- Preview: https://blissful-unicorn-479437--soft-shore-ky3c2mftk.framer.app
- Production: https://andremeloniphotography.co
- Main had zero pending changes at the captured baseline.

## Boundary

The repository entry point only creates a local review JSON file. It has no
Framer SDK, credentials, network calls, CMS mutation or publish capability.
Passing an approval-like environment variable cannot change that boundary.
A clean review plan is a proposal, never authorisation to release.

## Before any release

1. Obtain Andre's explicit approval of the exact verified preview/version and scope.
2. Re-read main and branch changes; compare them with the approved report. If
   either changed, reconcile and re-test before proceeding. Do not merge other branches.
3. Confirm the Mac scheduler and every other CMS writer cannot overwrite newer
   content. Do not assume this GitHub patch changes an independent Mac checkout.
4. Merge this safeguard PR only when authorised. Verify the installed workflow
   has no scheduled release, credentials, main writes or CMS publish step.
5. Release the approved Framer branch only, using Framer's supported controls.
   Confirm target, changed pages/components/CMS item and version before publishing.
6. Verify both production pages, metadata, canonical URLs, enquiry destinations,
   mobile layouts and HTTP responses after release. Record the actual version.

## Rollback

Keep the previous production version and the pre-change project/CMS snapshot.
If release verification fails, use Framer's version rollback to the recorded
previous production version. Do not replay the six historical GitHub bundles:
they contain outdated text, dates and image descriptions. Recheck affected URLs
after rollback and record what was restored.

## Current known limits

The snapshot is an audit record and expires for future proposals. Refresh it
read-only from the exact project and collection; never manufacture new timestamps
on old data. Runtime status of the separate Mac scheduler has not been verified.
No enquiry form submission or production publication was made during this work.
