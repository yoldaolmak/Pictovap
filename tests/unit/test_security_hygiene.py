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
            if fpath.name == "sample-output.json":
                continue
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

# ---------------------------------------------------------------------------
# 5. No disabled TLS/SSL certificate verification anywhere in src/
# ---------------------------------------------------------------------------

def test_no_disabled_ssl_verification():
    """
    No source file may disable TLS certificate verification
    (ssl.CERT_NONE, check_hostname = False, requests verify=False). Any of
    these exposes API credentials in transit to man-in-the-middle attacks.
    """
    forbidden = [
        r"CERT_NONE",
        r"check_hostname\s*=\s*False",
        r"verify\s*=\s*False",
    ]
    violations = []
    src_dir = REPO_ROOT / "src"
    for fpath in src_dir.rglob("*.py"):
        content = fpath.read_text(encoding="utf-8")
        for pattern in forbidden:
            if re.search(pattern, content):
                rel = fpath.relative_to(REPO_ROOT)
                violations.append(f"  {rel}: matches {pattern!r}")

    assert not violations, (
        "Disabled TLS/SSL verification found:\n" + "\n".join(violations)
    )


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


# ---------------------------------------------------------------------------
# 6. src/ and tests/ stay free of personal-legacy infrastructure
# ---------------------------------------------------------------------------

def test_src_and_tests_free_of_personal_legacy_references():
    """
    The legacy personal project ("Pictova") must not leak into the pipeline:
    no personal machine paths, personal site names, or personal-blog
    geography in src/ or tests/ Python files. The public GitHub repo URL is
    the only allowed appearance of the maintainer's handle. This has slipped
    past cleanup passes before, so it is enforced here permanently.
    """
    indicators = [
        "/users/",           # personal machine paths
        "downloads/",        # ad-hoc debug paths (e.g. ~/Downloads/IMG_*.jpeg)
        "gezievreni",        # personal site name
        "hamal",             # personal WordPress username
        "batum",             # personal-blog geography from the legacy slug engine
        "kapadokya",
        "gumusluk",
    ]
    violations = []
    for base in (REPO_ROOT / "src", REPO_ROOT / "tests"):
        for fpath in base.rglob("*.py"):
            if fpath.name == "test_security_hygiene.py":
                continue  # this file names the forbidden patterns themselves
            rel = fpath.relative_to(REPO_ROOT)
            for lineno, line in enumerate(
                fpath.read_text(encoding="utf-8").splitlines(), start=1
            ):
                lower = line.lower()
                for needle in indicators:
                    if needle in lower:
                        violations.append(f"  {rel}:{lineno}: contains {needle!r}")
                if "yoldaolmak" in lower and "github.com/yoldaolmak" not in lower:
                    violations.append(
                        f"  {rel}:{lineno}: personal handle outside repo URL"
                    )

    assert not violations, (
        "Personal-legacy references found in src/ or tests/:\n" + "\n".join(violations)
    )
