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


def test_api_plan_attach_uses_native_selection(monkeypatch):
    from src.vil.app import api

    monkeypatch.setattr(
        "src.vil.app.api.prepare_attach_request",
        lambda **payload: (
            {"site": "yoldaolmak", "post_id": 42, "source": "semantic", "location_query": "Roma", "count": 3},
            {"id": 42, "title": "Roma", "slug": "roma"},
            {"language": "tr", "people_first": True},
        ),
    )
    monkeypatch.setattr(
        "src.vil.app.api.build_attach_plan",
        lambda **kwargs: {"command": "plan", "status": "success", "selection": {"files": ["a.jpg"]}},
    )

    result = api.plan_attach({"site": "yoldaolmak", "post_id": 42})
    assert result["command"] == "plan"
    assert result["status"] == "success"
    assert result["selection"]["files"] == ["a.jpg"]


def test_cli_plan_command_outputs_structured_selection(monkeypatch, capsys):
    from src.vil.app import cli

    monkeypatch.setattr(
        cli,
        "plan_attach",
        lambda payload: {
            "command": "plan",
            "status": "success",
            "selection": {"source": "semantic", "files": ["roma-1.jpg", "roma-2.jpg"]},
        },
    )
    monkeypatch.setattr(sys, "argv", ["vil", "plan", "--site", "yoldaolmak", "--post", "123"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"command": "plan"' in output
    assert '"roma-1.jpg"' in output


def test_api_process_attach_returns_processed_images(monkeypatch):
    from src.vil.app import api

    monkeypatch.setattr(
        "src.vil.app.api.prepare_attach_request",
        lambda **payload: (
            {"site": "yoldaolmak", "post_id": 42, "source": "semantic", "location_query": "Roma", "count": 2},
            {"id": 42, "title": "Roma", "slug": "roma"},
            {"language": "tr", "people_first": False},
        ),
    )
    monkeypatch.setattr(
        "src.vil.app.api.build_process_result",
        lambda **kwargs: {"command": "process", "status": "success", "processed_images": ["a.webp"]},
    )

    result = api.process_attach({"site": "yoldaolmak", "post_id": 42})
    assert result["command"] == "process"
    assert result["status"] == "success"
    assert result["processed_images"] == ["a.webp"]


def test_cli_process_command_outputs_processed_images(monkeypatch, capsys):
    from src.vil.app import cli

    monkeypatch.setattr(
        cli,
        "process_attach",
        lambda payload: {
            "command": "process",
            "status": "success",
            "processed_images": ["roma-1_yo.webp"],
        },
    )
    monkeypatch.setattr(sys, "argv", ["vil", "process", "--site", "yoldaolmak", "--post", "123"])

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"command": "process"' in output
    assert '"roma-1_yo.webp"' in output
