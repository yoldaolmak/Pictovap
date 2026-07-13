"""
Tests for the Pictovap local demo.

Proves:
- demo module is importable
- run_demo() runs without any .env or credentials
- examples/sample-output.json is produced after the run
- all four primitives serialize correctly
- docs/README.md links point to files that exist
"""

import json
import os
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_README = REPO_ROOT / "docs" / "README.md"


# ---------------------------------------------------------------------------
# 1. Demo module is importable
# ---------------------------------------------------------------------------

def test_demo_module_importable():
    """The demo module must import without errors."""
    from pictovap import demo  # noqa: F401
    assert hasattr(demo, "run_demo"), "run_demo function must exist in demo module"


# ---------------------------------------------------------------------------
# 2. Demo runs without .env or credentials
# ---------------------------------------------------------------------------

def test_demo_runs_without_env(tmp_path, monkeypatch):
    """
    run_demo() must complete without any environment credentials.
    We strip any inherited credential env vars and verify the demo still runs.
    """
    credential_vars = [
        "WORDPRESS_URL", "WORDPRESS_USERNAME", "WORDPRESS_APP_PASSWORD",
        "UNSPLASH_ACCESS_KEY", "DEPOSITPHOTOS_API_KEY",
        "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
        "YO_VISUAL_MEMORY_DB", "LM_STUDIO_URL",
    ]
    for var in credential_vars:
        monkeypatch.delenv(var, raising=False)

    # Override output path so it writes to tmp_path and doesn't clobber examples/
    monkeypatch.chdir(tmp_path)

    from pictovap.demo import run_demo
    # Must not raise — if it does, the test fails with the actual exception
    run_demo()


# ---------------------------------------------------------------------------
# 3. sample-output.json is produced
# ---------------------------------------------------------------------------

def test_sample_output_produced(tmp_path, monkeypatch):
    """
    After running the demo, its default sample-output.json must exist and
    contain all four primitive keys.
    """
    monkeypatch.chdir(tmp_path)

    from pictovap.demo import run_demo
    run_demo()

    output_path = tmp_path / "sample-output.json"
    assert output_path.exists(), f"Expected {output_path} to exist after demo run"

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "visual_brief" in data, "Output must contain visual_brief"
    assert "fit_scores" in data, "Output must contain fit_scores"
    assert "provenance_packs" in data, "Output must contain provenance_packs"
    assert "cms_placement" in data, "Output must contain cms_placement"
    assert data["source_path"] == "sample-article.md"
    assert data["visual_brief"]["source_path"] == "sample-article.md"


# ---------------------------------------------------------------------------
# 4. All four primitives serialize correctly
# ---------------------------------------------------------------------------

def test_visual_brief_serializes():
    from pictovap.core.primitives import VisualBrief
    brief = VisualBrief(
        article_title="Test Article",
        topic="testing",
        sections=[{"heading": "Intro", "level": "h2"}],
        image_slots=[{"slot_id": "featured", "purpose": "featured_image", "preferred_type": "landscape"}],
    )
    data = brief.to_dict()
    assert data["article_title"] == "Test Article"
    assert data["topic"] == "testing"
    assert len(data["sections"]) == 1
    assert len(data["image_slots"]) == 1


def test_fit_score_serializes():
    from pictovap.core.primitives import FitScore
    score = FitScore(
        candidate_id="img-test",
        final_score=9.5,
        decision="selected",
        human_reason="Strong fit",
    )
    data = score.to_dict()
    assert data["candidate_id"] == "img-test"
    assert data["final_score"] == 9.5
    assert data["decision"] == "selected"


def test_provenance_pack_serializes():
    from pictovap.core.primitives import ProvenancePack
    pack = ProvenancePack(
        image_id="img-001",
        provider="local",
        original_filename="test.jpg",
        generated_filename="pictovap_test.webp",
        content_hash="abc123",
        slot_id="featured",
        placement_target="featured_image",
        generated_alt_text="A test scene",
        generated_caption="Test caption",
    )
    data = pack.to_dict()
    assert data["image_id"] == "img-001"
    assert data["provider"] == "local"
    assert "timestamp" in data
    assert data["timestamp"] is not None


def test_cms_placement_serializes():
    from pictovap.core.primitives import CMSPlacement, PlacementInstruction
    placement = CMSPlacement(
        article_id="test-article",
        adapter_target="mock",
        target_platform="demo",
        placements=[
            PlacementInstruction(
                slot_id="featured",
                output_path="pictovap_test.webp",
                target_section="",
                placement_strategy="featured",
                image_role="featured",
                alt_text="A test scene",
                caption="Test caption",
            )
        ],
    )
    data = placement.to_dict()
    assert data["article_id"] == "test-article"
    assert data["target_platform"] == "demo"
    assert len(data["placements"]) == 1
    assert data["placements"][0]["slot_id"] == "featured"


# ---------------------------------------------------------------------------
# 5. docs/README.md links point to existing files
# ---------------------------------------------------------------------------

def test_docs_readme_links_resolve():
    """
    Every relative markdown link in docs/README.md must point to a file
    that exists on disk.
    """
    assert DOCS_README.exists(), f"{DOCS_README} must exist"

    content = DOCS_README.read_text(encoding="utf-8")
    docs_dir = DOCS_README.parent

    # Match markdown links: [text](target) — only relative links (no http/https)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    broken = []

    for match in link_pattern.finditer(content):
        link_text, link_target = match.group(1), match.group(2)

        # Skip external links and anchors
        if link_target.startswith("http") or link_target.startswith("#"):
            continue

        # Strip fragment
        path_part = link_target.split("#")[0]
        if not path_part:
            continue

        resolved = (docs_dir / path_part).resolve()
        if not resolved.exists():
            broken.append(f"  [{link_text}]({link_target}) -> {resolved}")

    assert not broken, (
        f"docs/README.md contains {len(broken)} broken link(s):\n" +
        "\n".join(broken)
    )


# ---------------------------------------------------------------------------
# 6. Demo arguments (custom paths)
# ---------------------------------------------------------------------------

def test_demo_with_custom_paths(tmp_path):
    """Demo should accept custom article and output paths."""
    from pictovap.demo import run_demo
    
    # Create a dummy article
    custom_article = tmp_path / "custom-article.md"
    custom_article.write_text("# Custom Article\n\nSome text.", encoding="utf-8")
    
    custom_output = tmp_path / "custom-output.json"
    
    # Run demo
    run_demo(article_path_str=str(custom_article), output_path_str=str(custom_output))
    
    assert custom_output.exists(), "Custom output file must be created"
    data = json.loads(custom_output.read_text(encoding="utf-8"))
    assert data["visual_brief"]["article_title"] == "Custom Article", "Should parse the custom article"


def test_demo_missing_article_exits(capsys):
    """Demo should exit clearly if custom article doesn't exist."""
    from pictovap.demo import run_demo
    
    with pytest.raises(SystemExit) as exc_info:
        run_demo(article_path_str="/path/that/does/not/exist.md")
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Article not found" in captured.err


def test_demo_with_markdown_report(tmp_path):
    """Demo should optionally write a Markdown report that meets formatting requirements."""
    from pictovap.demo import run_demo
    
    custom_article = tmp_path / "custom-article.md"
    custom_article.write_text("# Markdown Test\n\nTesting the report.", encoding="utf-8")
    
    custom_output = tmp_path / "custom-output.json"
    custom_report = tmp_path / "custom-report.md"
    
    run_demo(
        article_path_str=str(custom_article),
        output_path_str=str(custom_output),
        report_path_str=str(custom_report)
    )
    
    assert custom_output.exists(), "JSON output must be created"
    assert custom_report.exists(), "Markdown report must be created"
    
    report_text = custom_report.read_text(encoding="utf-8")
    
    # Must contain sections
    assert "## Article" in report_text
    assert "## Visual Brief" in report_text
    assert "## CMS Placement Plan" in report_text
    assert "## Provenance" in report_text
    
    # Must contain the title
    assert "**Title:** Markdown Test" in report_text
    
    # Must not contain raw JSON dumped (a heuristic is no top-level brace or quoting)
    assert '{"visual_brief":' not in report_text
    assert '}' not in report_text  # Simple heuristic for raw JSON formatting
