"""Minimal HTTP server for the VIL application surface."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any, Callable, Dict, Tuple

from src.vil.app.api import attach_images, health_status, plan_attach, process_attach, review_post
from src.vil.app.state import job_registry


RouteHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _load_json_body(handler: BaseHTTPRequestHandler) -> Tuple[Dict[str, Any] | None, str | None]:
    raw_length = handler.headers.get("Content-Length", "0").strip() or "0"
    try:
        length = int(raw_length)
    except ValueError:
        return None, "invalid content-length"
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None, "invalid json body"
    if not isinstance(payload, dict):
        return None, "json body must be an object"
    return payload, None


def build_handler() -> type[BaseHTTPRequestHandler]:
    routes: Dict[Tuple[str, str], RouteHandler] = {
        ("GET", "/health"): lambda _payload: health_status(),
        ("POST", "/attach"): attach_images,
        ("POST", "/plan"): plan_attach,
        ("POST", "/process"): process_attach,
        ("POST", "/review"): review_post,
    }

    class VILRequestHandler(BaseHTTPRequestHandler):
        server_version = "VILHTTP/0.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {
                        "service": "vil",
                        "status": "ok",
                        "routes": [
                            {"method": "GET", "path": "/health"},
                            {"method": "POST", "path": "/attach"},
                            {"method": "POST", "path": "/plan"},
                            {"method": "POST", "path": "/process"},
                            {"method": "POST", "path": "/review"},
                            {"method": "GET", "path": "/jobs"},
                            {"method": "GET", "path": "/jobs/{job_id}"},
                            {"method": "POST", "path": "/jobs/attach"},
                        ],
                    },
                )
                return

            if self.path == "/jobs":
                _json_response(
                    self,
                    HTTPStatus.OK,
                    {"status": "ok", "jobs": job_registry.list_jobs()},
                )
                return

            if self.path.startswith("/jobs/"):
                job_id = self.path[len("/jobs/") :].strip()
                try:
                    job = job_registry.get_job(job_id)
                except KeyError:
                    _json_response(self, HTTPStatus.NOT_FOUND, {"status": "failed", "warning": "job not found"})
                    return
                _json_response(self, HTTPStatus.OK, {"status": "ok", "job": job})
                return

            route = routes.get(("GET", self.path))
            if route is None:
                _json_response(self, HTTPStatus.NOT_FOUND, {"status": "failed", "warning": "route not found"})
                return

            result = route({})
            code = HTTPStatus.OK if result.get("status") in {"ok", "success", "local"} else HTTPStatus.BAD_REQUEST
            _json_response(self, code, result)

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/jobs/attach":
                payload, error = _load_json_body(self)
                if error:
                    _json_response(self, HTTPStatus.BAD_REQUEST, {"status": "failed", "warning": error})
                    return
                job = job_registry.create_job(
                    kind="attach",
                    payload=payload or {},
                    runner=attach_images,
                )
                _json_response(self, HTTPStatus.ACCEPTED, {"status": "accepted", "job": job})
                return

            route = routes.get(("POST", self.path))
            if route is None:
                _json_response(self, HTTPStatus.NOT_FOUND, {"status": "failed", "warning": "route not found"})
                return

            payload, error = _load_json_body(self)
            if error:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"status": "failed", "warning": error})
                return

            try:
                result = route(payload or {})
            except Exception as exc:
                _json_response(
                    self,
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"status": "failed", "warning": str(exc), "path": self.path},
                )
                return

            code = HTTPStatus.OK if result.get("status") in {"ok", "success", "local"} else HTTPStatus.BAD_REQUEST
            _json_response(self, code, result)

    return VILRequestHandler


def serve(*, host: str = "127.0.0.1", port: int = 8040) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), build_handler())
    return server


__all__ = ["build_handler", "serve"]
