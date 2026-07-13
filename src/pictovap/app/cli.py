"""Pictovap CLI entrypoint.

Commands matching the public library API:
    demo    - run the credential-free example pipeline
    plan    - create a visual plan for a real article (pictovap.create_visual_plan)
    report  - render an existing JSON plan as a Markdown editor report
    plugins - list installed third-party adapter plugins
    scaffold - generate a standalone adapter plugin package
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from pictovap.demo import create_visual_plan, generate_report_from_file, run_demo
from pictovap.plugins import PluginError, iter_plugins
from pictovap.scaffold import ScaffoldError, scaffold_adapter


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pictovap")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Run the built-in credential-free example")

    plan = sub.add_parser("plan", help="Create a visual plan for a Markdown article")
    plan.add_argument("--article", required=True, help="Path to a Markdown article")
    plan.add_argument("--profile", help="Path to a Publisher Profile YAML")
    plan.add_argument("--output", help="Path to write the JSON output plan")
    plan.add_argument("--report", help="Path to write the Markdown report")

    report = sub.add_parser("report", help="Generate an editor-readable Markdown report from a plan")
    report.add_argument("--plan", required=True, help="Path to visual-plan.json")
    report.add_argument("--output", required=True, help="Path to write the output report.md")

    plugins = sub.add_parser("plugins", help="List installed third-party adapter plugins")
    plugins.add_argument("--kind", choices=("provider", "cms"), help="Filter by adapter kind")

    scaffold = sub.add_parser("scaffold", help="Generate a standalone adapter plugin package")
    scaffold.add_argument("kind", choices=("provider", "cms"), help="Adapter contract to implement")
    scaffold.add_argument("name", help="Adapter name, for example wikimedia or hugo")
    scaffold.add_argument("--output", default=".", help="Parent directory for the generated package")
    scaffold.add_argument("--force", action="store_true", help="Overwrite scaffold-owned files")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
        return 0

    if args.command == "plan":
        try:
            plan_output = create_visual_plan(
                article=args.article,
                profile=args.profile,
                output=args.output,
                report=args.report,
            )
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error running plan: {e}", file=sys.stderr)
            return 1
        if not args.output:
            _print_json(plan_output)
        return 0

    if args.command == "report":
        try:
            generate_report_from_file(args.plan, args.output)
            return 0
        except Exception as e:
            print(f"Error generating report: {e}", file=sys.stderr)
            return 1

    if args.command == "plugins":
        try:
            _print_json({"plugins": [plugin.to_dict() for plugin in iter_plugins(args.kind)]})
            return 0
        except PluginError as e:
            print(f"Error discovering plugins: {e}", file=sys.stderr)
            return 1

    if args.command == "scaffold":
        try:
            root = scaffold_adapter(
                args.kind,
                args.name,
                output=args.output,
                force=args.force,
            )
        except (OSError, ScaffoldError) as e:
            print(f"Error creating scaffold: {e}", file=sys.stderr)
            return 1
        print(root)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
