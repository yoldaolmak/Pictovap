"""Canonical CLI entrypoint for VIL."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from pictova.app.health import run_health_check
from pictova.app.jobs import run_attach_job
from pictova.app.api import plan_attach, process_attach
from pictova.app.server import serve
from pictova.providers.wordpress import fetch_post_context, guard_post_media


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pictova")
    sub = parser.add_subparsers(dest="command", required=True)

    attach = sub.add_parser("attach")
    attach.add_argument("--site", default="yoldaolmak")
    attach.add_argument("--post", type=int, required=True)
    attach.add_argument("--count", type=int, default=4)
    attach.add_argument("--name")
    attach.add_argument(
        "--source",
        default="semantic",
        choices=["semantic", "auto", "vil", "local", "unsplash", "deposit"],
    )
    attach.add_argument("--query")
    attach.add_argument("--location-query")
    attach.add_argument("--content-filter")
    attach.add_argument("--lang", default="tr")
    attach.add_argument("--people-first", action="store_true")
    attach.add_argument("--engine", default="legacy", choices=["legacy", "native"])
    attach.add_argument("--heading", help="Force all images after this heading text")
    attach.add_argument("--heading-level", type=int, default=0, help="Heading level (2 or 3)")

    review = sub.add_parser("review")
    review.add_argument("--site", default="yoldaolmak")
    review.add_argument("--post", type=int, required=True)

    guard = sub.add_parser("guard")
    guard.add_argument("--site", default="yoldaolmak")
    guard.add_argument("--post", type=int, required=True)
    guard_mode = guard.add_mutually_exclusive_group()
    guard_mode.add_argument("--repair", action="store_true")
    guard_mode.add_argument("--adopt", action="store_true")
    guard.add_argument("--media-id", dest="media_ids", action="append", type=int)

    plan = sub.add_parser("plan")
    plan.add_argument("--site", default="yoldaolmak")
    plan.add_argument("--post", type=int, required=True)
    plan.add_argument("--count", type=int, default=4)
    plan.add_argument("--name")
    plan.add_argument(
        "--source",
        default="semantic",
        choices=["semantic", "auto", "vil", "local", "unsplash", "deposit"],
    )
    plan.add_argument("--query")
    plan.add_argument("--location-query")
    plan.add_argument("--content-filter")
    plan.add_argument("--lang", default="tr")
    plan.add_argument("--people-first", action="store_true")
    plan.add_argument("--heading", help="Force all images after this heading text")
    plan.add_argument("--heading-level", type=int, default=0, help="Heading level (2 or 3)")

    process = sub.add_parser("process")
    process.add_argument("--site", default="yoldaolmak")
    process.add_argument("--post", type=int, required=True)
    process.add_argument("--count", type=int, default=4)
    process.add_argument("--name")
    process.add_argument(
        "--source",
        default="semantic",
        choices=["semantic", "auto", "vil", "local", "unsplash", "deposit"],
    )
    process.add_argument("--query")
    process.add_argument("--location-query")
    process.add_argument("--content-filter")
    process.add_argument("--lang", default="tr")
    process.add_argument("--people-first", action="store_true")
    process.add_argument("--heading", help="Force all images after this heading text")
    process.add_argument("--heading-level", type=int, default=0, help="Heading level (2 or 3)")

    serve_cmd = sub.add_parser("serve")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8040)

    sub.add_parser("health")
    return parser


def _attach_args_to_payload(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "site": args.site,
        "post_id": args.post,
        "count": args.count,
        "name": args.name,
        "source": args.source,
        "query": args.query,
        "location_query": args.location_query,
        "content_filter": args.content_filter,
        "language": args.lang,
        "people_first": args.people_first,
        "engine": getattr(args, "engine", "legacy"),
        "heading": getattr(args, "heading", None),
        "heading_level": getattr(args, "heading_level", 0) or 0,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "attach":
        try:
            result = run_attach_job(**_attach_args_to_payload(args))
        except Exception as exc:
            result = {"command": "attach", "status": "failed", "warnings": [str(exc)]}
        _print_json(result)
        return 0 if result.get("status") in {"success", "local"} else 1

    if args.command == "review":
        try:
            result = {
                "command": "review",
                "status": "success",
                "post_context": fetch_post_context(args.post, site=args.site),
            }
        except Exception as exc:
            result = {
                "command": "review",
                "status": "failed",
                "post_context": {},
                "warnings": [str(exc)],
            }
        _print_json(result)
        return 0 if result["status"] == "success" else 1

    if args.command == "guard":
        result = guard_post_media(
            args.post,
            site=args.site,
            repair=args.repair,
            adopt=args.adopt,
            media_ids=args.media_ids,
        )
        _print_json(result)
        return 0 if result.get("status") == "success" else 1

    if args.command == "plan":
        result = plan_attach(_attach_args_to_payload(args))
        _print_json(result)
        return 0 if result.get("status") == "success" else 1

    if args.command == "process":
        result = process_attach(_attach_args_to_payload(args))
        _print_json(result)
        return 0 if result.get("status") == "success" else 1

    if args.command == "health":
        result = run_health_check()
        _print_json(result)
        return 0 if result.get("status") == "ok" else 1

    if args.command == "serve":
        server = serve(host=args.host, port=args.port)
        try:
            _print_json(
                {
                    "command": "serve",
                    "status": "ok",
                    "host": args.host,
                    "port": args.port,
                }
            )
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
