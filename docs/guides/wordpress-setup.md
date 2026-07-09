# WordPress Setup

## Enabling Application Passwords

Pictovap uses WordPress Application Passwords for authentication. These are separate from your account password and can be revoked independently.

1. Log in to WordPress admin
2. Go to **Users → Profile**
3. Scroll to **Application Passwords**
4. Enter a name (e.g., `Pictovap`) and click **Add New Application Password**
5. Copy the generated password — it is shown only once

The password looks like: `xxxx xxxx xxxx xxxx xxxx xxxx`

## Configuring Pictova

In `.env`:

```bash
WP_USER=your-wp-username
WP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

Spaces in the password are fine — WordPress accepts both formats.

## Site Profiles

Pictovap uses site profiles to store per-site configuration beyond credentials. The profile for `yoldaolmak` is at `src/pictova/profiles/yoldaolmak.py`.

A profile defines:

| Field | Default | Description |
|-------|---------|-------------|
| `site_url` | — | Base URL of the WordPress site |
| `wp_path` | — | Server path to WordPress root (for wp-cli) |
| `default_count` | 4 | Images per post |
| `people_first` | false | Prefer images with human subjects |
| `source_priority` | `["semantic", "unsplash"]` | Sources in order of preference |
| `block_type` | `"image"` | Gutenberg block type for placement |
| `featured_image` | true | Set first image as featured image |

## Adding a New Site

Create `src/pictova/profiles/mysite.py` following the existing `yoldaolmak.py` structure. Then use `--site mysite` in any command.

See [Site Profiles Reference](../reference/profiles.md) for the full profile schema.

## WordPress Permissions

The Application Password user needs:

- `upload_files` capability (Editor or Author role minimum)
- `edit_posts` capability to update post content

Contributor role is insufficient — use Editor or create a custom role.

## HTTPS Requirement

Pictovap enforces HTTPS for all WordPress connections. `http://` URLs will be rejected at validation time.
