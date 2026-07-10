# WordPress Setup

You do not need WordPress credentials to run the local demo. The demo runs entirely in a dry-run / plan-first workflow, creating local JSON and Markdown reports.

For real WordPress publishing, Pictovap will need a WordPress URL, username, and Application Password or another supported authentication method. These credentials must live in `.env` or another local secret store. They must never be committed to the repository.

The WordPress adapter should consume a CMS Placement plan. WordPress is one adapter, not the conceptual center of Pictovap.

## Configuration

In your project root, copy `.env.example` to `.env` and fill in the values:

```env
WP_URL=https://yoursite.com
WP_USER=your-wordpress-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

### Application Passwords

WordPress requires an Application Password, not your standard login password. You can generate this in your WordPress Admin dashboard under `Users -> Profile -> Application Passwords`.

## Implementation Status

- **Implemented**: Dry-run local JSON placement plans.
- **Implemented**: WordPress publishing adapter (extracted from production).
- **Planned**: Ghost and Strapi publishing adapters.
