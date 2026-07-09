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
    from pictova.app import jobs
    from pictova.engine import attach as attach_engine

    class FakeOrchestrator:
        def run_pipeline(self, **kwargs):
            assert kwargs["location_query"] == "roma"
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
    assert result["request"]["location_query"] == "roma"
    assert result["constraints"]["language"] == "tr"
    assert result["constraints"]["people_first"] is True
    assert result["uploaded_media_ids"] == [11, 12]
    assert result["inserted_blocks"] == 2
    assert result["rejected_assets"][0]["file"] == "c.webp"


def test_cli_review_command_outputs_post_context(monkeypatch, capsys):
    from pictova.app import cli

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
    from pictova.app import jobs
    from pictova.engine import attach as attach_engine

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


def test_derive_location_query_uses_destination_from_branded_title():
    from pictova.engine.attach import derive_location_query

    assert derive_location_query({"slug": "", "title": "Karaburun Gezi Rehberi — Penovate"}) == "karaburun"
    assert derive_location_query({"slug": "", "title": "Karaburun Gezi Rehberi: Karaburun Gezilecek Yerler"}) == "karaburun"


def test_cli_parser_exposes_native_local_and_auto_sources():
    from pictova.app.cli import build_parser

    parser = build_parser()
    local_args = parser.parse_args([
        "attach", "--post", "267970", "--source", "local", "--query", "/tmp/a.jpg",
    ])
    auto_args = parser.parse_args(["plan", "--post", "267970", "--source", "auto"])
    guard_args = parser.parse_args(["guard", "--post", "267970", "--repair"])

    assert local_args.source == "local"
    assert auto_args.source == "auto"
    assert guard_args.repair is True


def test_api_attach_images_reuses_job_contract(monkeypatch):
    from pictova.app import api

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
    from pictova.app import api

    monkeypatch.setattr(
        "pictova.app.api.prepare_attach_request",
        lambda **payload: (
            {"site": "yoldaolmak", "post_id": 42, "source": "semantic", "location_query": "Roma", "count": 3},
            {"id": 42, "title": "Roma", "slug": "roma"},
            {"language": "tr", "people_first": True},
        ),
    )
    monkeypatch.setattr(
        "pictova.app.api.build_attach_plan",
        lambda **kwargs: {"command": "plan", "status": "success", "selection": {"files": ["a.jpg"]}},
    )

    result = api.plan_attach({"site": "yoldaolmak", "post_id": 42})
    assert result["command"] == "plan"
    assert result["status"] == "success"
    assert result["selection"]["files"] == ["a.jpg"]


def test_cli_plan_command_outputs_structured_selection(monkeypatch, capsys):
    from pictova.app import cli

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
    from pictova.app import api

    monkeypatch.setattr(
        "pictova.app.api.prepare_attach_request",
        lambda **payload: (
            {"site": "yoldaolmak", "post_id": 42, "source": "semantic", "location_query": "Roma", "count": 2},
            {"id": 42, "title": "Roma", "slug": "roma"},
            {"language": "tr", "people_first": False},
        ),
    )
    monkeypatch.setattr(
        "pictova.app.api.build_process_result",
        lambda **kwargs: {"command": "process", "status": "success", "processed_images": ["a.webp"]},
    )

    result = api.process_attach({"site": "yoldaolmak", "post_id": 42})
    assert result["command"] == "process"
    assert result["status"] == "success"
    assert result["processed_images"] == ["a.webp"]


def test_cli_process_command_outputs_processed_images(monkeypatch, capsys):
    from pictova.app import cli

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
    from pictova.app import jobs
    from pictova.engine import attach as attach_engine

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
        "finalize_publish_assets",
        lambda **kwargs: (
            ["roma-semantik-1.webp", "roma-semantik-2.webp"],
            {
                "roma-semantik-1.webp": {"title": "Roma Semantik 1"},
                "roma-semantik-2.webp": {"title": "Roma Semantik 2"},
            },
            {},
        ),
    )
    seen = {}
    monkeypatch.setattr(
        attach_engine,
        "publish_processed_images",
        lambda **kwargs: seen.update(kwargs) or {
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
    assert seen["processed_images"] == ["roma-semantik-1.webp", "roma-semantik-2.webp"]


def test_run_attach_job_native_engine_blocks_low_quality_assets(monkeypatch):
    from pictova.app import jobs
    from pictova.engine import attach as attach_engine

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


def test_insert_before_first_h2_preserves_gutenberg_heading_block():
    from pictova.services import wordpress

    content = """<!-- wp:paragraph -->\n<p>Intro</p>\n<!-- /wp:paragraph -->\n\n<!-- wp:heading -->\n<h2 class=\"wp-block-heading\">Baslik</h2>\n<!-- /wp:heading -->\n"""
    block = "<!-- wp:image --><figure>Gorsel</figure><!-- /wp:image -->"

    updated = wordpress._insert_before_first_h2(content, block)

    assert "<!-- wp:heading -->\n<h2 class=\"wp-block-heading\">Baslik</h2>\n<!-- /wp:heading -->" in updated
    assert "<!-- wp:heading -->\n\n<!-- wp:image -->" not in updated
    assert updated.index(block) < updated.index("<!-- wp:heading -->")


def test_build_native_metadata_map_raises_without_any_vision_source(monkeypatch):
    """Basic fallback yasak — hiç kaynak yoksa RuntimeError fırlatılmalı."""
    from pictova.engine import metadata as metadata_engine
    import pictova.engine.vision_chain as vc

    # has_any_vision_source metadata_engine'e direkt import edildiği için oradan patch et
    monkeypatch.setattr(metadata_engine, "has_any_vision_source", lambda: False)

    import pytest
    with pytest.raises(RuntimeError, match="Hiç vision kaynağı bulunamadı"):
        metadata_engine.build_native_metadata_map(
            ["roma-1_yo.webp"],
            post_context={"title": "Roma Rehberi", "slug": "roma-rehberi"},
        )


def test_http_server_health_route_returns_json():
    from pictova.app.server import serve

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
    from pictova.app import server as server_module

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


def test_http_server_guard_route_uses_api_contract(monkeypatch):
    from pictova.app import server as server_module

    monkeypatch.setattr(
        server_module,
        "guard_post",
        lambda payload: {
            "command": "guard",
            "status": "success",
            "state": "healthy",
            "request": payload,
        },
    )

    server = server_module.serve(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        request = Request(
            f"http://{host}:{port}/guard",
            data=json.dumps({"site": "yoldaolmak", "post_id": 267970}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["status"] == "success"
        assert payload["state"] == "healthy"
        assert payload["request"]["post_id"] == 267970
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_server_attach_job_route_returns_job_and_result(monkeypatch):
    from pictova.app import server as server_module
    from pictova.app.state import job_registry

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
