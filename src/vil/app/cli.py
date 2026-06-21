"""Canonical CLI entrypoint for VIL."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from src.vil.app.health import run_health_check
from src.vil.app.jobs import run_attach_job
from src.vil.providers.wordpress import fetch_post_context


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vil")
    sub = parser.add_subparsers(dest="command", required=True)

    attach = sub.add_parser("attach")
    attach.add_argument("--site", default="yoldaolmak")
    attach.add_argument("--post", type=int, required=True)
    attach.add_argument("--count", type=int, default=4)
    attach.add_argument("--name")
    attach.add_argument("--source", default="semantic", choices=["semantic", "vil", "unsplash"])
    attach.add_argument("--query")
    attach.add_argument("--location-query")
    attach.add_argument("--content-filter")
    attach.add_argument("--lang", default="tr")
    attach.add_argument("--people-first", action="store_true")

    review = sub.add_parser("review")
    review.add_argument("--site", default="yoldaolmak")
    review.add_argument("--post", type=int, required=True)

    sub.add_parser("health")
    return parser


def _attach_args_to_payload(args: argparse.Namespace) -> Dict[str, Any]:
    content_filter = args.content_filter
    if args.people_first and not content_filter:
        content_filter = "insan"
    location_query = args.location_query
    if args.source == "semantic" and not location_query:
        location_query = str(args.post)
    return {
        "site": args.site,
        "post_id": args.post,
        "count": args.count,
        "name": args.name,
        "source": args.source,
        "query": args.query,
        "location_query": location_query,
        "content_filter": content_filter,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "attach":
        result = run_attach_job(**_attach_args_to_payload(args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") in {"success", "local"} else 1

    if args.command == "review":
        print(json.dumps(fetch_post_context(args.post, site=args.site), ensure_ascii=False, indent=2))
        return 0

    if args.command == "health":
        result = run_health_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "ok" else 1

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
