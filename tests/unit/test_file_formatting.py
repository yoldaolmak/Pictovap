import pytest
from pathlib import Path

def line_count(path):
    p = Path(path)
    if not p.exists():
        return 0
    return len(p.read_text(encoding="utf-8").splitlines())

def test_public_files_are_not_collapsed():
    minimum_lines = {
        "README.md": 40,
        "Makefile": 20,
        ".github/workflows/ci.yml": 40,
        "docs/README.md": 20,
        "docs/ARCHITECTURE.md": 40,
        "examples/profiles/sample-publisher.yaml": 25,
        "src/pictova/demo.py": 100,
        "tests/unit/test_demo.py": 80,
        "tests/unit/test_file_formatting.py": 20,
        "pyproject.toml": 20,
    }
    repo_root = Path(__file__).parent.parent.parent
    for rel_path, minimum in minimum_lines.items():
        path = repo_root / rel_path
        assert line_count(path) >= minimum, f"{rel_path} appears collapsed or malformed (lines: {line_count(path)}, expected at least {minimum})"
