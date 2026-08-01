import json

from pictovap.ecosystem import (
    build_ecosystem_match,
    ecosystem_tool_kinds,
    render_ecosystem_markdown,
    render_supported_tool_kinds,
)


def test_build_ecosystem_match_returns_copyable_markdown_to_wordpress_packet():
    packet = build_ecosystem_match(
        "markdown-to-wordpress",
        project_name="md2wp",
        repository_url="https://github.com/example/md2wp",
    )

    assert packet["status"] == "compatible"
    assert packet["tool_kind"] == "markdown-to-wordpress"
    assert packet["project_name"] == "md2wp"
    assert packet["repository_url"] == "https://github.com/example/md2wp"
    assert "WordPress authentication" in packet["owned_by_target"]
    assert "provenance" in packet["pictovap_role"]
    assert "Pictovap" in packet["readme_section"]
    assert "https://github.com/yoldaolmak/Pictovap" in packet["readme_section"]
    assert packet["readme_section"].count("https://github.com/yoldaolmak/Pictovap") == 1
    assert "docs-only" in packet["pr_body"]
    assert any("clicks the Pictovap link" in item for item in packet["anti_spam_checklist"])


def test_build_ecosystem_match_accepts_aliases():
    packet = build_ecosystem_match("md2wp", project_name="Importer")

    assert packet["tool_kind"] == "markdown-to-wordpress"


def test_render_ecosystem_markdown_contains_pr_body_and_checklist():
    packet = build_ecosystem_match("ai-draft", project_name="Draft Tool")
    rendered = render_ecosystem_markdown(packet)

    assert "# Pictovap Ecosystem Integration" in rendered
    assert "## README Section" in rendered
    assert "## Pull Request Body" in rendered
    assert "- [ ] The target repository benefits" in rendered
    assert "Draft Tool creates review-ready drafts" in rendered


def test_supported_tool_kinds_are_json_safe_and_renderable():
    kinds = ecosystem_tool_kinds()
    encoded = json.dumps(kinds)
    rendered = render_supported_tool_kinds(kinds)

    assert "markdown-to-wordpress" in encoded
    assert "`ai-draft`" in rendered
