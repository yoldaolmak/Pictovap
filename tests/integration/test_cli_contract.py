import sys
from pathlib import Path
import json
import threading
import time
from urllib.request import Request, urlopen


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


def test_run_attach_job_native_engine_uses_native_pipeline(monkeypatch):
    from src.vil.app import jobs
    from src.vil.engine import attach as attach_engine

    monkeypatch.setattr(
        attach_engine,
        "fetch_post_context",
        lambda post_id, site="yoldaolmak": {"id": post_id, "title": "Roma", "slug": "roma"},
    )
    monkeypatch.setattr(
        attach_engine,
        "resolve_source_images",
        lambda **kwargs: {"source": "semantic", "files": ["roma-1.jpg", "roma-2.jpg"]},
    )
    monkeypatch.setattr(
        attach_engine,
        "process_selected_images",
        lambda files, **kwargs: {
            "processed_images": ["roma-1_yo.webp", "roma-2_yo.webp"],
            "processed_details": {},
            "panoramic_images": {},
            "work_dir": "/tmp/vil-native",
        },
    )
    monkeypatch.setattr(
        attach_engine,
        "build_native_metadata_map",
        lambda image_files, **kwargs: (
            {path: {"title": path, "alt": path, "caption": path, "description": path} for path in image_files},
            ["vision metadata enabled"],
        ),
    )
    monkeypatch.setattr(
        attach_engine,
        "publish_processed_images",
        lambda **kwargs: {
            "uploaded": [{"media_id": 91}, {"media_id": 92}],
            "failed": [],
            "content_update": {"inserted": 2},
        },
    )

    result = jobs.run_attach_job(
        site="yoldaolmak",
        post_id=264459,
        count=2,
        source="semantic",
        location_query="Roma",
        content_filter=None,
        language="tr",
        people_first=False,
        engine="native",
    )

    assert result["status"] == "success"
    assert result["uploaded_media_ids"] == [91, 92]
    assert result["inserted_blocks"] == 2
    assert result["selected_assets"] == ["roma-1.jpg", "roma-2.jpg"]
    assert "vision metadata enabled" in result["warnings"][0]


def test_run_attach_job_native_engine_blocks_low_quality_assets(monkeypatch):
    from src.vil.app import jobs
    from src.vil.engine import attach as attach_engine

    monkeypatch.setattr(
        attach_engine,
        "fetch_post_context",
        lambda post_id, site="yoldaolmak": {"id": post_id, "title": "Roma Rehberi", "slug": "roma-rehberi"},
    )
    monkeypatch.setattr(
        attach_engine,
        "resolve_source_images",
        lambda **kwargs: {"source": "semantic", "files": ["roma-1.jpg"]},
    )
    monkeypatch.setattr(
        attach_engine,
        "process_selected_images",
        lambda files, **kwargs: {
            "processed_images": ["roma-1_yo.webp"],
            "processed_details": {
                "roma-1_yo.webp": {
                    "final_size": (1200, 750),
                    "brightness": 0.5,
                    "saturation": 0.2,
                    "contrast": 0.2,
                    "color_temp": 0.0,
                    "file_size_kb": 120,
                }
            },
            "panoramic_images": {},
            "work_dir": "/tmp/vil-native",
        },
    )
    monkeypatch.setattr(
        attach_engine,
        "build_native_metadata_map",
        lambda image_files, **kwargs: (
            {
                "roma-1_yo.webp": {
                    "title": "Kısa",
                    "alt": "short",
                    "caption": "short",
                    "description": "tiny",
                }
            },
            ["basic metadata fallback only"],
        ),
    )
    monkeypatch.setattr(
        attach_engine,
        "publish_processed_images",
        lambda **kwargs: {
            "uploaded": [],
            "failed": [],
            "content_update": {"inserted": 0},
        },
    )

    result = jobs.run_attach_job(
        site="yoldaolmak",
        post_id=264459,
        count=1,
        source="semantic",
        location_query="Roma",
        content_filter=None,
        language="tr",
        people_first=False,
        engine="native",
    )

    assert result["status"] == "success"
    assert result["uploaded_media_ids"] == []
    assert result["rejected_assets"][0]["file"] == "roma-1_yo.webp"
    assert "title too short" in result["rejected_assets"][0]["errors"]


def test_build_native_metadata_map_falls_back_without_credentials(monkeypatch):
    from src.vil.engine import metadata as metadata_engine

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    metadata_dict, warnings = metadata_engine.build_native_metadata_map(
        ["roma-1_yo.webp"],
        location_hint="Roma",
        post_context={"title": "Roma Rehberi", "slug": "roma-rehberi"},
    )

    assert "roma-1_yo.webp" in metadata_dict
    assert "basic metadata fallback only" in warnings[0]


def test_http_server_health_route_returns_json():
    from src.vil.app.server import serve

    server = serve(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(f"http://{host}:{port}/health") as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["status"] in {"ok", "fail"}
        assert "modules" in payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_server_attach_route_uses_api_contract(monkeypatch):
    from src.vil.app import server as server_module

    monkeypatch.setattr(
        server_module,
        "attach_images",
        lambda payload: {"command": "attach", "status": "success", "request": payload},
    )

    server = server_module.serve(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        request = Request(
            f"http://{host}:{port}/attach",
            data=json.dumps({"site": "yoldaolmak", "post_id": 264459}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["status"] == "success"
        assert payload["request"]["post_id"] == 264459
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_server_attach_job_route_returns_job_and_result(monkeypatch):
    from src.vil.app import server as server_module
    from src.vil.app.state import job_registry

    monkeypatch.setattr(
        server_module,
        "attach_images",
        lambda payload: {"command": "attach", "status": "success", "request": payload},
    )

    server = server_module.serve(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        request = Request(
            f"http://{host}:{port}/jobs/attach",
            data=json.dumps({"site": "yoldaolmak", "post_id": 264459}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert payload["status"] == "accepted"
        job_id = payload["job"]["job_id"]

        final_job = None
        for _ in range(20):
            with urlopen(f"http://{host}:{port}/jobs/{job_id}") as response:
                polled = json.loads(response.read().decode("utf-8"))
            if polled["job"]["status"] in {"success", "failed"}:
                final_job = polled["job"]
                break
            time.sleep(0.05)

        assert final_job is not None
        assert final_job["status"] == "success"
        assert final_job["result"]["request"]["post_id"] == 264459

        with urlopen(f"http://{host}:{port}/jobs") as response:
            jobs_payload = json.loads(response.read().decode("utf-8"))
        assert any(item["job_id"] == job_id for item in jobs_payload["jobs"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
