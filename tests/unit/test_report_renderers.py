from __future__ import annotations

import pytest

from pictovap.renderers import HTMLReportRenderer, MarkdownReportRenderer
from pictovap.testing import ContractViolation, assert_report_renderer_contract


def _plan():
    return {
        "visual_brief": {"article_title": "A <safe> title"},
        "profile": {"brand": "Example Publisher"},
        "provenance_packs": [{
            "slot_id": "featured", "provider": "local", "license_status": "CC0",
            "generated_alt_text": "A scene", "image_id": "image-1",
            "placement_target": "featured", "generated_caption": "A scene.",
            "source_type": "local", "source_url": None, "local_source_path": "scene.jpg",
            "attribution": None, "content_hash": "abc123",
        }],
        "fit_scores": {"featured": [{"candidate_id": "image-1", "final_score": 9, "human_reason": "Good fit", "decision": "selected"}]},
        "cms_placement": {"placements": [{
            "image_role": "featured", "placement_strategy": "featured",
            "target_section": "", "output_path": "image.webp",
        }]},
    }


@pytest.mark.parametrize("renderer", [MarkdownReportRenderer(), HTMLReportRenderer()])
def test_builtin_renderers_satisfy_the_public_contract(renderer):
    report = assert_report_renderer_contract(renderer, plan=_plan())
    assert "Pictovap Visual Plan" in report


def test_html_renderer_escapes_article_content():
    report = HTMLReportRenderer().render(_plan())
    assert "A &lt;safe&gt; title" in report


def test_contract_rejects_non_renderer():
    with pytest.raises(ContractViolation, match="ReportRenderer"):
        assert_report_renderer_contract(object())
