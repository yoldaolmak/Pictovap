# Installation

Full setup guide covering all Pictovap components.

## System Requirements

- macOS or Linux
- Python 3.9 or higher
- WordPress 5.8+ with Application Passwords enabled (only if using the WordPress CMS adapter)

## Step 1: Clone the Repository

```bash
git clone <repo-url> pictova
cd pictova
```

## Step 2: Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

The `-e` flag installs Pictovap in editable mode and registers the `pictova` CLI command.

## Step 4: Configure Environment

```bash
cp .env.example .env
```

### Minimum Configuration

```bash
# WordPress — required for attach
WP_USER=your-wordpress-username
WP_PASSWORD=your-app-password

# At least one image source
UNSPLASH_ACCESS_KEY=your-unsplash-key
```

### Full Configuration

See [Configuration Reference](../reference/configuration.md) for all available variables.

## Step 5: Verify Installation

```bash
pictova health
```

```json
{"status": "ok", "service": "pictova"}
```

```bash
python3 -m pytest -q
```

Expected: `19 passed, 1 warning` (or better).

## Optional: HTTP Service

To run Pictovap as an HTTP service:

```bash
pictova serve --host 127.0.0.1 --port 8040
```

See [HTTP API Reference](../reference/http-api.md) for endpoint documentation.

## Troubleshooting

**`pictova: command not found`**  
Make sure your virtualenv is active and you ran `pip install -e .`.

**`review` returns an auth error**  
Verify `WP_USER` and `WP_PASSWORD`. Application Password format: `xxxx xxxx xxxx xxxx xxxx xxxx`.

**`plan` returns empty candidates**  
Check that at least one entry in the profile's `image_sources` is actually configured
(e.g. `UNSPLASH_ACCESS_KEY` set, or `PICTOVAP_LOCAL_IMAGE_DIR` pointing at a real directory).
