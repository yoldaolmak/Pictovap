"""Documentation integrity checks without prescribed prose or headings."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_DOCS = [
    "AGENTS.md",
    "README.md",
    "docs/README.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
    "docs/architecture/core-product-boundary.md",
    "docs/concepts/decision-pack.md",
    "docs/release-status.md",
]


def test_primary_document_links_resolve():
    """Readers should never be sent to missing relative repository files."""
    links = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken = []
    for relative in PRIMARY_DOCS:
        path = REPO_ROOT / relative
        assert path.is_file(), relative
        for match in links.finditer(path.read_text(encoding="utf-8")):
            target = match.group(2).split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "/", "#")):
                continue
            if not (path.parent / target).resolve().is_file():
                broken.append(f"{relative}: {target}")

    assert not broken, "Broken relative documentation links: " + ", ".join(broken)


def test_checkout_versions_agree():
    """Actual package and project metadata must publish the same version."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (REPO_ROOT / "src/actovisio_framework/__init__.py").read_text(
        encoding="utf-8"
    )
    project = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    package = re.search(r'^__version__ = "([^"]+)"$', package_init, re.MULTILINE)
    assert project is not None and package is not None
    assert project.group(1) == package.group(1)


def test_release_notes_identify_development_checkout():
    """The documented checkout version must match the version in the code."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    release_status = (REPO_ROOT / "docs/release-status.md").read_text(
        encoding="utf-8"
    )
    project = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    assert project is not None
    assert project.group(1) in release_status
