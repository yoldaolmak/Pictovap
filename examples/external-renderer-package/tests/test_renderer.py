from pictovap.testing import assert_report_renderer_contract
from pictovap_external_html_review import ExternalHTMLReviewRenderer


def test_renderer_satisfies_pictovap_contract():
    report = assert_report_renderer_contract(
        ExternalHTMLReviewRenderer(),
        plan={
            "visual_brief": {"article_title": "Harbor guide"},
            "cms_placement": {"placements": []},
        },
    )

    assert report.startswith("<!doctype html>")
    assert "Harbor guide" in report
