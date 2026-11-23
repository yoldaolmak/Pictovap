# WordPress Gutenberg Review Sidebar (reference)

This installable WordPress reference plugin offers an editorial review **draft**
inside Gutenberg for an existing post. It is not a publishing plugin or the
separate Enterprise Product. It registers no REST route, post metadata, media
upload, or save hook. Nothing is sent from the sidebar to a Pictovap server.
The imported source stays in the editor's browser memory until the editor
explicitly downloads a decisions file.

## Install and try

1. Copy the complete `examples/wordpress-review-sidebar/` directory into
   `wp-content/plugins/pictovap-review-sidebar/` on a disposable WordPress
   instance and activate it.
2. Use the development Pictovap package to create a Visual Plan for an
   existing Gutenberg post. The plan's article ID **must** match that post.
   For a permissioned read, use `pictovap plan --wordpress-post 42 --wordpress-site publisher --output plan.json`.
3. Create the original immutable review input:

   `pictovap review-pack --plan plan.json --output pending-pack.json`

4. Open post #42 in Gutenberg. Import `pending-pack.json` in the
   **Pictovap Review** sidebar. The sidebar is available only to users
   authorized to edit that specific existing post.
5. Accept or reject proposed images, or import *existing* replacement evidence
   JSON for a scored, non-rejected candidate. That JSON must already contain
   atomic `candidate_id`, `provenance`, and `placement` fields.
   Unknown rights remain unknown; a source search preview is not a license.
6. Inspect the per-slot **not yet Core-validated** preview and download the
   locally generated review decisions JSON. WordPress content is untouched.
7. Use the original pack and downloaded draft to obtain a valid reviewed
   Decision Pack and a portable comparison:

   `pictovap review-import --pack pending-pack.json --decisions review-decisions.json --output reviewed.json --preview reviewed.md`

Python Core verifies the exact source bytes' SHA-256 fingerprint, review
completeness, article identity, candidate bindings and replacement evidence.
The result remains `application.status=not_applied`, not a publish receipt.

## Boundaries

- This is a **reference implementation**, not a tested live deployment.
  It requires an authorized Gutenberg editor trial before production use.
- Editor identity is included as a descriptive claim in the downloaded draft,
  **not** independently authenticated by the Python CLI.
- No background fetch, upload, CMS write, database, or paid model is added.
  Standard WordPress scripts power the sidebar; no npm build is required.
- New-post screens are deliberately unsupported until a stable post ID exists.
- The sidebar's checks improve usability; Python Core is the authoritative
  schema/transition validator. The browser cannot grant image rights.
- Asset URLs are not automatically fetched: previews may be unlicensed or
  signed URLs that leak private credentials. All input evidence is potentially
  private; do not attach these files to public issues.
- There is no drag-and-drop placement, automatic asset purchase, or live image
  verification. WordPress publishing remains a separately authorized process.

## Offline verification

`node --test examples/wordpress-review-sidebar/tests/review-model.test.cjs`

`pytest tests/unit/test_review_bridge.py -q`

`php -l examples/wordpress-review-sidebar/pictovap-review-sidebar.php`

CI executes the Node and Python tests. A successful UI render and a real editor
review in a supported WordPress version remain separate acceptance gates.
