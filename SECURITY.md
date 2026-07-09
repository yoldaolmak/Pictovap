# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ Current |
| < 0.2   | ❌ No longer supported |

## Reporting a Vulnerability

If you discover a security vulnerability in Pictovap, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email the maintainers directly at: hello@yoldaolmak.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix if available

## Credential Policy

- **Never commit `.env` files.** Only `.env.example` is tracked, and it must contain empty placeholders only.
- Adapter credentials (CMS, image sources, model providers) must be loaded from environment variables or external secret stores at runtime.
- Tests must not require real credentials. The demo runs entirely credential-free.
- The credential-free demo must remain the default experience — no external APIs, no paid providers, no private databases.

## Public Configuration Policy

- `.env.example` must contain only empty placeholder values (`KEY=` with no value).
- No real URLs, usernames, API keys, tokens, passwords, or local paths may appear in `.env.example`.
- No private provider-specific setup instructions may appear in public documentation.
- Provider references in source code (e.g., `os.environ.get("UNSPLASH_ACCESS_KEY")`) are acceptable — they read from the user's local environment and never expose values.

## Adapter Credential Handling

All adapters (WordPress, Unsplash, DepositPhotos, Ghost, Strapi) follow the same pattern:

1. Credentials are read from environment variables at runtime.
2. If credentials are missing, the adapter raises a clear error or is skipped gracefully.
3. No credentials are hardcoded in source code.
4. No credentials are stored in tracked configuration files.

## Secret Scanning

The repository includes automated secret scanning via:

- `tests/unit/test_security_hygiene.py` — scans public-facing files for private patterns on every test run.
- `make security-check` — dedicated Makefile target to run security hygiene tests.

These tests check for:
- Personal local paths
- Real WordPress/CMS credentials
- Non-empty credential values in `.env.example`
- Private provider-specific notes
- Vendor-specific model provider references in public docs

## Scope

Pictovap processes image files and communicates with CMS APIs. Security concerns may include:

- Credential exposure through configuration files
- Malicious image file processing
- CMS API authentication token handling
- Path traversal in file operations
- Provider API key leakage

## Response

We aim to acknowledge security reports within 48 hours and provide a fix or mitigation plan within 7 days for confirmed vulnerabilities.
