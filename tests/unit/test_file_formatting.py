"""Structural file guards, independent of arbitrary document line counts."""

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CRITICAL_FILES = (
    ".gitignore",
    "README.md",
    "AGENTS.md",
    "Makefile",
    ".github/workflows/ci.yml",
    "docs/README.md",
    "docs/ROADMAP.md",
    "docs/ARCHITECTURE.md",
    "src/actovisio_framework/demo.py",
    "tests/unit/test_demo.py",
    "pyproject.toml",
)


@pytest.mark.parametrize("relative", CRITICAL_FILES)
def test_repository_files_are_readable_not_collapsed(relative):
    """Detect missing, empty, binary, or single-line accidental overwrites."""
    path = REPO_ROOT / relative
    assert path.is_file(), relative
    contents = path.read_text(encoding="utf-8")
    assert contents.strip(), relative
    assert "\x00" not in contents, relative
    assert "\n" in contents, relative


def test_gitignore_packaged_data_exception_matches_current_package():
    """Repository ignore rules must not hide intended package resources."""
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert chr(96) * 3 not in text
    assert "!src/actovisio_framework/data/" in text
    assert "!src/actovisio_framework/data/**" in text
    assert ".pytest_cache/" in text


def test_distribution_has_one_canonical_package_and_console_script():
    """Check real package discovery and entry-point configuration."""
    package_roots = sorted(
        path.name
        for path in (REPO_ROOT / "src").iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    )
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts_section = pyproject.split("[project.scripts]", 1)[1].split("[", 1)[0]
    scripts = [line.strip() for line in scripts_section.splitlines() if line.strip()]

    assert package_roots == ["actovisio_framework"]
    assert scripts == ['actovisio-framework = "actovisio_framework.app.cli:main"']
