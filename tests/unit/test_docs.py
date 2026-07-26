import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_all_markdown_links():
    files_to_check = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "README.md",
        REPO_ROOT / "docs" / "release-checklist.md",
        REPO_ROOT / "docs" / "adoption-playbook.md",
        REPO_ROOT / "docs" / "release-notes" / "v0.2.0.md",
        REPO_ROOT / "docs" / "contributing" / "starter-issues.md",
    ]

    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    broken = []

    for file_path in files_to_check:
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")
        base_dir = file_path.parent

        for match in link_pattern.finditer(content):
            link_target = match.group(2)

            # Skip external links and internal fragment anchors
            if link_target.startswith("http") or link_target.startswith("#"):
                continue

            path_part = link_target.split("#")[0]
            if not path_part:
                continue

            resolved = (base_dir / path_part).resolve()
            if not resolved.exists():
                broken.append(f"Broken link in {file_path.name}: {link_target} -> {resolved}")

    assert not broken, "\n".join(broken)


def test_contributor_docs_use_current_fast_gate():
    docs = [
        "CONTRIBUTING.md",
        "docs/contributing/adapter-sprint.md",
        "docs/contributing/first-adapter-pr.md",
        "docs/contributing/wordpress-gutenberg-minisprint.md",
        "docs/guides/installation.md",
        ".github/pull_request_template.md",
    ]

    for rel_path in docs:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert "make contributor-smoke" in text, rel_path
        assert "make contribution-check" in text, rel_path


def test_issue_copy_templates_use_current_contributor_gate():
    text = (REPO_ROOT / "docs" / "contributing" / "issue_templates.md").read_text(
        encoding="utf-8"
    )

    assert "make contributor-smoke" in text
    assert "make contribution-check" in text
    assert "pytest tests/unit -q" not in text
