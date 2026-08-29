import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_all_markdown_links():
    files_to_check = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docs" / "README.md",
        REPO_ROOT / "docs" / "release-checklist.md",
        REPO_ROOT / "docs" / "release-status.md",
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


def test_release_status_matches_checkout_version():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (REPO_ROOT / "src" / "pictovap" / "__init__.py").read_text(
        encoding="utf-8"
    )
    release_status = (REPO_ROOT / "docs" / "release-status.md").read_text(
        encoding="utf-8"
    )

    project_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    package_version = re.search(r'^__version__ = "([^"]+)"$', package_init, re.MULTILINE)

    assert project_version and package_version
    assert project_version.group(1) == package_version.group(1)
    assert f"Version declared by the checkout: **{project_version.group(1)}**" in release_status
    assert "Publication state: **unreleased**" in release_status
    assert "pypi.org/project/pictovap/0.12.0" in release_status
    assert "releases/tag/v0.12.0" in release_status


def test_contributor_docs_use_current_fast_gate():
    docs = [
        "CONTRIBUTING.md",
        "docs/contributing/adapter-sprint.md",
        "docs/contributing/first-pr-kits.md",
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


def test_external_validation_docs_use_pypi_and_safe_feedback():
    docs = [
        ".github/ISSUE_TEMPLATE/external_validation.md",
        "docs/adoption-playbook.md",
        "docs/external-tester-message.md",
        "docs/issues/02-try-your-own-article-feedback.md",
    ]

    for rel_path in docs:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert "python -m pip install --upgrade pictovap" in text, rel_path
        assert "pictovap feedback --plan my-plan.json --format markdown" in text, rel_path
        assert "issues/new?template=external_validation.md" in text, rel_path
        assert "pictovap==0.7.12" not in text, rel_path


def test_external_tester_message_uses_issue_form_not_legacy_thread():
    text = (REPO_ROOT / "docs" / "external-tester-message.md").read_text(
        encoding="utf-8"
    )

    assert "github.com/yoldaolmak/Pictovap/issues/8" not in text


def test_first_pr_kits_remain_small_and_actionable():
    text = (REPO_ROOT / "docs" / "contributing" / "first-pr-kits.md").read_text(
        encoding="utf-8"
    )

    for issue_number in ("#40", "#41", "#42"):
        assert issue_number in text
    assert "PR size:" in text
    assert "Do not touch:" in text
    assert ".venv/bin/python -m pytest --no-cov tests/unit/test_wordpress_input.py -q" in text
    assert "make contribution-check" in text
