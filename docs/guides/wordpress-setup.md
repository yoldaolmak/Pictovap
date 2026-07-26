# WordPress Setup

This guide explains how Pictovap interacts with WordPress, when credentials
are required, how to configure environment variables safely, and how to
troubleshoot common connection issues.

## What WordPress integration means

Pictovap is designed to be CMS-agnostic. Its core engine converts written
content into a structured `CMSPlacement` plan.

A WordPress adapter can read this `CMSPlacement` plan and translate it into
native WordPress actions: uploading processed images to the WordPress Media
Library, setting alt text and captions, attaching media items to the post, and
inserting Gutenberg image blocks after designated section headings.

## What does not need WordPress credentials

You do not need WordPress credentials for local planning and evaluation
workflows:

* `pictovap demo` — runs entirely locally with zero external API calls or credentials.
* `pictovap plan --article article.md` — parses a local Markdown article
  without contacting WordPress.
* `pictovap report` — generates editor-readable Markdown reports locally.
* **JSON and Markdown report generation** — all core planning artifacts are
  created and stored on your local disk.

## What needs WordPress credentials

WordPress credentials are needed when Pictovap contacts a live WordPress
instance, such as:

* Reading live Gutenberg posts directly via REST API (`context=edit`).
* Uploading image assets to the WordPress Media Library.
* Updating WordPress post content with inserted Gutenberg image blocks.
* Setting featured images on live posts.

## Recommended credential method

Pictovap recommends using **WordPress Application Passwords**.

Application Passwords allow external tools to authenticate via HTTP Basic
Authentication without exposing your primary account password. You can create,
inspect, and revoke Application Passwords at any time under **WordPress Admin
→ Users → Profile → Application Passwords**.

## Example `.env`

Credentials must live in a local `.env` file or environment variables.
**Never commit `.env` to source control.**

Create a `.env` file in your project root using empty placeholders:

```env
# Default WordPress credentials
WP_URL=
WP_USER=
WP_APP_PASSWORD=

# Named site credentials (optional multi-site pattern: <SITE>_URL)
MYBLOG_URL=
MYBLOG_USER=
MYBLOG_APP_PASSWORD=
```

## Example publisher profile

Publisher profiles define brand preferences and layout rules. Profiles must never store credentials.

Example `examples/profiles/wordpress-example.yaml`:

```yaml
schema_version: 1
profile_id: wordpress-example
brand_name: Example WordPress Publisher
cms_type: wordpress
language: en
language_mode: fallback

cms:
  type: wordpress
  mode: dry-run
  credentials: env

image_sources:
  - local
  - unsplash

output_rules:
  format: webp
  max_width: 1200
  quality: 85
```

## Dry-run first

Always validate your visual plan in dry-run mode before modifying a live WordPress site:

1. Generate a local plan and report:

   ```bash
   pictovap plan \
     --article article.md \
     --output plan.json \
     --report report.md
   ```

2. Review candidate scores, licensing, alt text, and placement instructions in
   the Markdown report.
3. Verify that target section headings in the plan match the post's actual
   Gutenberg structure.

To read a live Gutenberg post without modifying it:

```bash
pictovap plan \
  --wordpress-post 42 \
  --wordpress-site publisher \
  --output plan.json \
  --report report.md
```

`--wordpress-site publisher` reads `PUBLISHER_URL`, `PUBLISHER_USER`, and
`PUBLISHER_APP_PASSWORD`. Omit it to use the default `WP_` variables.

## Live publishing

Live publishing sends HTTP requests to your WordPress REST API endpoints
(`/wp-json/wp/v2/media` and `/wp-json/wp/v2/posts/<id>`).

* **Execution path**: `WordPressUploader` in
  `src/pictovap/services/wordpress.py` executes media upload, attachment,
  block generation, and post updates.
* **Safety controls**: Pictovap verifies post modification dates before
  committing content updates to prevent overwriting concurrent edits
  (`post_media_guard`).
* **Prerequisites**: valid `WP_URL`, `WP_USER`, and `WP_APP_PASSWORD`
  environment variables, plus an account with `edit_posts` and `upload_files`
  capabilities.

## Security rules

1. **Never commit `.env`** — ensure `.env` is listed in `.gitignore`.
2. **Never commit Application Passwords** — treat generated passwords like private keys.
3. **Never place credentials in profile YAML files** — publisher profiles are
   shareable configuration schemas.
4. **Use environment variables** — pass credentials via standard env vars or a local secret manager.
5. **Use mocks in test suites** — all unit and integration tests must mock network interactions.

## Troubleshooting

### Authentication failed (HTTP 401)
* Verify that `WP_USER` matches your exact WordPress username.
* Ensure `WP_APP_PASSWORD` contains no typos or missing spaces. WordPress
  formats Application Passwords with spaces, for example
  `xxxx xxxx xxxx xxxx`.
* Check if your host blocks `Authorization` header forwarding in `.htaccess` or Nginx config.

### Invalid site URL
* Ensure `WP_URL` includes the protocol (`https://`) and no trailing slash
  (for example, `https://example.com`).
* Verify the WordPress REST API root is accessible at `https://example.com/wp-json/`.

### REST API disabled
* Confirm that plugins or security suites are not blocking the `/wp-json/wp/v2/` REST endpoints.

### Insufficient user permissions (HTTP 403)
* Ensure the authenticating user has the `Editor` or `Administrator` role, or
  explicit `upload_files` and `edit_posts` capabilities.

### Application Passwords unavailable
* Application Passwords require HTTPS unless running on `localhost`. Ensure SSL
  is active on your site.
* Check if a security plugin has disabled Application Passwords globally.

### Media upload blocked
* Verify that your WordPress upload directory (`wp-content/uploads/`) has write permissions.
* Ensure WebP or target image formats are allowed by your WordPress installation.

### Gutenberg placement mismatch
* Check that heading text in your article exactly matches H2/H3 text in your Gutenberg post.
* Review the generated `report.md` to confirm placement target headings before publishing.
