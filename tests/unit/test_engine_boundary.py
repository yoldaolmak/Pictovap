"""The planning engine must stay silent, and the terminal view must come from the plan.

These are contract tests for the Core/presentation split: if the engine ever
prints again, or the demo starts narrating decisions it re-derives instead of
reading them from the artifact, a terminal view can silently disagree with the
plan an editor signs off on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pictovap import api, demo
from pictovap.core.profile import PublisherProfile
from pictovap.data.demo_candidates import MOCK_CANDIDATES
from pictovap.engine.planner import PLAN_LABEL, build_visual_plan


ARTICLE = Path(__file__).resolve().parents[2] / "examples" / "articles" / "travel-guide.md"


@pytest.fixture
def plan() -> dict:
    return build_visual_plan(
        ARTICLE,
        PublisherProfile.get_default_profile(),
        use_real_sources=False,
        fallback_candidates=MOCK_CANDIDATES,
        fallback_mode="demo",
    )


def test_engine_writes_nothing_to_stdout(capsys, plan):
    assert capsys.readouterr().out == ""
    assert plan["provenance_packs"]


def test_engine_writes_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build_visual_plan(
        ARTICLE,
        PublisherProfile.get_default_profile(),
        use_real_sources=False,
        fallback_candidates=MOCK_CANDIDATES,
        fallback_mode="demo",
    )
    assert list(tmp_path.iterdir()) == []


def test_engine_holds_no_fixture_of_its_own():
    """Without caller-supplied fallback candidates, an empty pool stays empty."""
    plan = build_visual_plan(
        ARTICLE,
        PublisherProfile.get_default_profile(),
        use_real_sources=False,
    )
    assert plan["candidates_evaluated"] == 0
    assert plan["provenance_packs"] == []
    assert plan["runtime"]["provider"]["mode"] == "profile"


def test_plan_label_does_not_claim_to_be_a_demo(plan):
    assert plan["pipeline"] == PLAN_LABEL
    assert "demo" not in plan["pipeline"].lower()


def test_console_view_is_derived_from_the_plan_alone(tmp_path, plan):
    """Rendering a stored plan reproduces the live view, byte for byte."""
    stored = tmp_path / "plan.json"
    stored.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    reloaded = json.loads(stored.read_text(encoding="utf-8"))
    assert demo.render_plan_console(reloaded) == demo.render_plan_console(plan)
    assert demo.render_plan_summary(reloaded) == demo.render_plan_summary(plan)


def test_console_view_reports_the_licenses_the_artifact_records(plan):
    rendered = demo.render_plan_console(plan)
    for pack in plan["provenance_packs"]:
        assert f"License: {pack['license_status']}" in rendered
    assert "LicenseType." not in rendered


def test_demo_module_exposes_no_second_public_api():
    """The stable planning API lives in `pictovap.api` and nowhere else."""
    assert not hasattr(demo, "create_visual_plan")
    assert not hasattr(demo, "create_wordpress_visual_plan")
    assert callable(api.create_visual_plan)
    assert callable(api.create_wordpress_visual_plan)
