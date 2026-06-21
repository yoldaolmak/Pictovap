import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_run_attach_job_derives_location_and_constraints(monkeypatch):
    from src.vil.app import jobs
    from src.vil.engine import attach as attach_engine

    class FakeOrchestrator:
        def run_pipeline(self, **kwargs):
            assert kwargs["location_query"] == "Roma Gezi Rehberi"
            assert kwargs["content_filter"] == "insan"
            return {
                "site": kwargs["site"],
                "post_id": kwargs["post_id"],
                "status": "success",
                "steps": {
                    "images_loaded": {"files": ["a.webp", "b.webp"]},
                    "quality_gate": {"blocked": [{"file": "c.webp", "errors": ["watermark"]}]},
                    "upload_complete": {
                        "uploaded": [{"media_id": 11}, {"media_id": 12}],
                        "failed": [],
                        "content_update": {"inserted": 2},
                    },
                },
            }

    monkeypatch.setattr(
        attach_engine,
        "YOOrchestrator",
        FakeOrchestrator,
    )
    monkeypatch.setattr(
        attach_engine,
        "fetch_post_context",
        lambda post_id, site="yoldaolmak": {"id": post_id, "title": "Roma Gezi Rehberi", "slug": "roma-gezi-rehberi"},
    )

    result = jobs.run_attach_job(
        site="yoldaolmak",
        post_id=264459,
        count=4,
        source="semantic",
        location_query=None,
        content_filter=None,
        language="tr",
        people_first=True,
    )

    assert result["status"] == "success"
    assert result["request"]["location_query"] == "Roma Gezi Rehberi"
    assert result["constraints"]["language"] == "tr"
    assert result["constraints"]["people_first"] is True
    assert result["uploaded_media_ids"] == [11, 12]
    assert result["inserted_blocks"] == 2
    assert result["rejected_assets"][0]["file"] == "c.webp"


def test_cli_review_command_outputs_post_context(monkeypatch, capsys):
    from src.vil.app import cli

    monkeypatch.setattr(
        cli,
        "fetch_post_context",
        lambda post_id, site="yoldaolmak": {"id": post_id, "title": "Savsat", "slug": "savsat"},
    )
    monkeypatch.setattr(sys, "argv", ["vil", "review", "--site", "yoldaolmak", "--post", "123"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"title": "Savsat"' in output


def test_run_attach_job_fails_when_semantic_query_cannot_be_derived(monkeypatch):
    from src.vil.app import jobs
    from src.vil.engine import attach as attach_engine

    monkeypatch.setattr(
        attach_engine,
        "fetch_post_context",
        lambda post_id, site="yoldaolmak": {"id": post_id, "title": "", "slug": ""},
    )

    result = jobs.run_attach_job(
        site="yoldaolmak",
        post_id=264459,
        count=4,
        source="semantic",
        location_query=None,
        content_filter=None,
        language="tr",
        people_first=False,
    )

    assert result["status"] == "failed"
    assert result["selected_assets"] == []
    assert "location_query could not be derived" in result["warnings"][0]


def test_api_attach_images_reuses_job_contract(monkeypatch):
    from src.vil.app import api

    monkeypatch.setattr(
        api,
        "run_attach_job",
        lambda **payload: {"command": "attach", "status": "success", "request": payload},
    )

    result = api.attach_images({"site": "yoldaolmak", "post_id": 42})
    assert result["command"] == "attach"
    assert result["status"] == "success"
    assert result["request"]["post_id"] == 42
