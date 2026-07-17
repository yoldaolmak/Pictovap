"""Pictovap CLI entrypoint.

Commands matching the public library API:
    demo    - run the credential-free example pipeline
    plan    - create a visual plan for a real article (pictovap.create_visual_plan)
    report  - render an existing JSON plan as a Markdown editor report
    plugins - list installed third-party adapter plugins
    scaffold - generate a standalone adapter plugin package
    doctor  - validate installed plugins and selected adapter configuration
    publish - execute a visual plan through an installed CMS plugin
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Sequence

from pictovap.app.runtime import (
    AdapterConstructionError,
    PipelineRunner,
    RuntimeConfigurationError,
    parse_adapter_options,
)
from pictovap.demo import generate_report_from_file, run_demo
from pictovap.plugins import PluginError, iter_plugins
from pictovap.scaffold import ScaffoldError, scaffold_adapter


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pictovap")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Run the built-in credential-free example")

    plan = sub.add_parser("plan", help="Create a visual plan from an article or WordPress post")
    plan_input = plan.add_mutually_exclusive_group(required=True)
    plan_input.add_argument("--article", help="Path to a Markdown article")
    plan_input.add_argument("--wordpress-post", type=int, help="WordPress Gutenberg post ID")
    plan.add_argument("--wordpress-site", default="demo", help="WordPress credential prefix/site name")
    plan.add_argument("--profile", help="Path to a Publisher Profile YAML")
    plan.add_argument("--output", help="Path to write the JSON output plan")
    plan.add_argument("--report", help="Path to write the Markdown report")
    plan.add_argument("--provider", help="Installed provider plugin entry-point name")
    plan.add_argument(
        "--provider-option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Provider constructor option; use KEY=@ENV_VAR for secrets",
    )

    publish = sub.add_parser("publish", help="Execute a visual plan through a CMS plugin")
    publish.add_argument("--plan", required=True, help="Path to visual-plan.json")
    publish.add_argument("--cms", required=True, help="Installed CMS plugin entry-point name")
    publish.add_argument(
        "--cms-option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="CMS constructor option; use KEY=@ENV_VAR for secrets",
    )
    publish.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show exact placement operations without calling CMSAdapter.place",
    )

    doctor = sub.add_parser("doctor", help="Check plugin discovery and adapter configuration")
    doctor.add_argument("--provider", help="Provider plugin to construct")
    doctor.add_argument("--cms", help="CMS plugin to construct")
    doctor.add_argument("--provider-option", action="append", default=[], metavar="KEY=VALUE")
    doctor.add_argument("--cms-option", action="append", default=[], metavar="KEY=VALUE")

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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runner = PipelineRunner()

    if args.command == "demo":
        run_demo()
        return 0

    if args.command == "plan":
        try:
            options = parse_adapter_options(args.provider_option)
            if args.wordpress_post is not None:
                plan_output = runner.plan_wordpress_post(
                    post_id=args.wordpress_post, site=args.wordpress_site,
                    profile=args.profile, output=args.output, report=args.report,
                    provider=args.provider, provider_options=options,
                )
            else:
                plan_output = runner.plan(
                    article=args.article, profile=args.profile, output=args.output,
                    report=args.report, provider=args.provider, provider_options=options,
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

    if args.command == "publish":
        try:
            result = runner.publish(
                plan=args.plan,
                cms=args.cms,
                cms_options=parse_adapter_options(args.cms_option),
                dry_run=args.dry_run,
            )
            _print_json(result)
            return 0
        except (FileNotFoundError, ValueError, PluginError, AdapterConstructionError) as e:
            print(f"Error publishing plan: {e}", file=sys.stderr)
            return 1

    if args.command == "doctor":
        try:
            result = runner.doctor(
                provider=args.provider,
                cms=args.cms,
                provider_options=parse_adapter_options(args.provider_option),
                cms_options=parse_adapter_options(args.cms_option),
            )
            _print_json(result)
            return 0 if result["status"] == "ready" else 1
        except (RuntimeConfigurationError, PluginError, AdapterConstructionError) as e:
            print(f"Error checking plugins: {e}", file=sys.stderr)
            return 1

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
