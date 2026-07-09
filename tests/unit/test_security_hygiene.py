"""
Security hygiene tests for Pictovap.

Scans public-facing files for private credentials, personal paths,
and provider-specific secrets that must not appear in a public repo.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Files/dirs that are part of the public surface
PUBLIC_DIRS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CONTRIBUTING.md",
    REPO_ROOT / "SECURITY.md",
    REPO_ROOT / "CHANGELOG.md",
    REPO_ROOT / "docs",
    REPO_ROOT / "examples",
    REPO_ROOT / ".github",
    REPO_ROOT / ".env.example",
]

# Allowed yoldaolmak reference locations (case-study, profile, pyproject author)
YOLDAOLMAK_ALLOWED_FILES = {
    "pyproject.toml",          # author email
    "PKG-INFO",                # auto-generated from pyproject
    "yoldaolmak.md",           # case study
    "yoldaolmak.yaml",         # profile
}


def _collect_public_files():
    """Gather all text files in public-facing directories."""
    files = []
    for entry in PUBLIC_DIRS:
        if entry.is_file() and entry.exists():
            files.append(entry)
        elif entry.is_dir() and entry.exists():
            for f in entry.rglob("*"):
                if f.is_file() and f.suffix in {".md", ".yml", ".yaml", ".txt", ".json", ".toml", ".cfg", ".env"}:
                    files.append(f)
    return files


# ---------------------------------------------------------------------------
# 1. No private credentials in .env.example
# ---------------------------------------------------------------------------

class TestEnvExample:
    """Validate .env.example contains only empty placeholders."""

    @pytest.fixture
    def env_content(self):
        env_path = REPO_ROOT / ".env.example"
        assert env_path.exists(), ".env.example must exist"
        return env_path.read_text(encoding="utf-8")

    def test_no_real_wordpress_url(self, env_content):
        assert "yoldaolmak.com" not in env_content

    def test_no_real_wordpress_user(self, env_content):
        assert "hamal" not in env_content

    def test_no_personal_paths(self, env_content):
        assert "/Users/yoldaolmak" not in env_content

    def test_no_claude_references(self, env_content):
        lower = env_content.lower()
        assert "claude" not in lower
        assert "anthropic" not in lower

    def test_no_gemini_key(self, env_content):
        assert "GEMINI_API_KEY" not in env_content

    def test_values_are_empty(self, env_content):
        """Every KEY=VALUE line must have an empty value (KEY= with nothing after)."""
        for line in env_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                assert value.strip() == "" or value.strip() in {
                    "wordpress", "sample-publisher"
                }, f"Non-empty credential value found: {key}={value}"

    def test_no_absolute_path_values(self, env_content):
        for line in env_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if "=" in stripped:
                _, _, value = stripped.partition("=")
                assert not value.strip().startswith("/"), (
                    f"Absolute path found in .env.example: {stripped}"
                )

    def test_no_real_url_values(self, env_content):
        for line in env_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if "=" in stripped:
                _, _, value = stripped.partition("=")
                assert "https://" not in value and "http://" not in value, (
                    f"Real URL found in .env.example: {stripped}"
                )


# ---------------------------------------------------------------------------
# 2. No private credentials in public docs
# ---------------------------------------------------------------------------

class TestPublicDocsSecurity:
    """Scan public-facing docs for forbidden private patterns."""

    FORBIDDEN_PATTERNS = [
        (r"/Users/yoldaolmak", "personal local path"),
        (r"WP_USER=hamal", "real WordPress username"),
        (r"WP_URL=https://yoldaolmak\.com", "real WordPress URL"),
        (r"Authorization:\s*Bearer\s+\S{10,}", "bearer token with real value"),
    ]

    def test_no_forbidden_patterns_in_public_docs(self):
        files = _collect_public_files()
        violations = []
        for fpath in files:
            try:
                content = fpath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for pattern, description in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, content):
                    rel = fpath.relative_to(REPO_ROOT)
                    violations.append(f"  {rel}: {description} ({pattern})")

        assert not violations, (
            f"Private patterns found in public docs:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 3. No non-empty credential placeholders in public config files
# ---------------------------------------------------------------------------

class TestNoLeakedCredentials:
    """Ensure no credential values are set in tracked config files."""

    CREDENTIAL_PATTERNS = [
        r"UNSPLASH_ACCESS_KEY=\S+",
        r"DEPOSITPHOTOS_API_KEY=\S+",
        r"CMS_APP_PASSWORD=\S+",
        r"GEMINI_API_KEY=\S+",
        r"ANTHROPIC_API_KEY=\S+",
        r"OPENAI_API_KEY=\S+",
        r"GHOST_ADMIN_API_KEY=\S+",
        r"STRAPI_API_TOKEN=\S+",
        r"dp_apikey=\S+",
    ]

    def test_no_filled_credentials_in_env_example(self):
        env_path = REPO_ROOT / ".env.example"
        if not env_path.exists():
            pytest.skip(".env.example not found")
        content = env_path.read_text(encoding="utf-8")
        for pattern in self.CREDENTIAL_PATTERNS:
            match = re.search(pattern, content)
            assert match is None, f"Credential value found: {match.group()}"


# ---------------------------------------------------------------------------
# 4. yoldaolmak references only in allowed locations
# ---------------------------------------------------------------------------

def test_yoldaolmak_references_only_in_allowed_locations():
    """
    yoldaolmak may appear in pyproject.toml (author email),
    case-study docs, or profile configs — but nowhere else
    as a private credential or personal path.
    """
    violations = []
    for fpath in (REPO_ROOT / "docs").rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.name in YOLDAOLMAK_ALLOWED_FILES:
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        if "/Users/yoldaolmak" in content:
            rel = fpath.relative_to(REPO_ROOT)
            violations.append(f"  {rel}: contains personal path /Users/yoldaolmak")

    assert not violations, (
        "Personal path references found outside allowed files:\n" + "\n".join(violations)
    )
