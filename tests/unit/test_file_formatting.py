"""
Test guard: verify that public repository files have not been collapsed
into single-line or malformed blobs by automated tooling.

Each file must have at least its expected minimum number of physical lines.
"""

import pytest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent

MINIMUM_LINES = {
    ".gitignore": 40,
    "README.md": 40,
    "Makefile": 20,
    ".github/workflows/ci.yml": 40,
    "docs/README.md": 20,
    "docs/ARCHITECTURE.md": 40,
    "examples/profiles/sample-publisher.yaml": 25,
    "src/pictovap/demo.py": 120,
    "tests/unit/test_demo.py": 80,
    "tests/unit/test_file_formatting.py": 25,
    "pyproject.toml": 30,
}


def line_count(path):
    """Return the number of physical lines in the file."""
    p = Path(path)
    if not p.exists():
        return 0
    return len(p.read_text(encoding="utf-8").splitlines())


@pytest.mark.parametrize(
    "rel_path,minimum",
    list(MINIMUM_LINES.items()),
    ids=list(MINIMUM_LINES.keys()),
)
def test_public_file_not_collapsed(rel_path, minimum):
    """Each public file must have at least {minimum} physical lines."""
    path = REPO_ROOT / rel_path
    actual = line_count(path)
    assert actual >= minimum, (
        f"{rel_path} appears collapsed or malformed: "
        f"{actual} lines, expected at least {minimum}"
    )


def test_gitignore_packaged_data_exception_matches_current_package():
    """The root ignore rules must not hide package data contributors need to add."""
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "```" not in text
    assert "src/pictova/data" not in text
    assert "!src/pictovap/data/" in text
    assert "!src/pictovap/data/**" in text
    assert ".pytest_cache/" in text
