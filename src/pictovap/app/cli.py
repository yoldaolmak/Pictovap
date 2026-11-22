"""Pictovap CLI entrypoint.

Commands matching the public library API:
    demo    - run the credential-free example pipeline
    plan    - create a visual plan for a real article (pictovap.create_visual_plan)
    report  - render an existing JSON plan as a Markdown editor report
    plugins - list installed third-party adapter plugins
    scaffold - generate a standalone adapter plugin package
    doctor  - validate installed plugins and selected adapter configuration
    publish - execute a visual plan through an installed CMS plugin
    feedback - create an anonymous validation summary from a plan
    audit    - review a plan for editorial and integration readiness
    benchmark - run the deterministic golden corpus benchmark
    registry - list built-in and installed adapters
    explain - render the proof-carrying intent decisions from a plan
    diff     - compare two serialized visual plans without rerunning providers
    ecosystem - generate adjacent-project integration packets
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Sequence

from pictovap import __version__
from pictovap.app.runtime import (
    AdapterConstructionError,
    PipelineRunner,
    RuntimeConfigurationError,
    construct_plugin,
    parse_adapter_options,
)
from pictovap.core.states import DoctorStatus, PublishStatus
from pictovap.decision_pack import (
    build_decision_pack,
    transition_decision_pack_review,
    validate_decision_pack,
)
from pictovap.review import preview_decision_pack, render_review_preview
from pictovap.demo import run_demo
from pictovap.engine.reporting import generate_report_from_file
from pictovap.feedback import render_feedback_markdown, summarize_plan
from pictovap.conformance import AdapterCheckError, check_adapter
from pictovap.audit import audit_visual_plan, render_audit_markdown
from pictovap.benchmark import benchmark_to_json, render_benchmark_markdown, run_corpus_benchmark
from pictovap.registry import registry_payload, registry_to_json, render_registry_markdown
from pictovap.intent import intent_proof_to_json, render_intent_markdown
from pictovap.plan_diff import diff_visual_plans, plan_diff_to_json, render_plan_diff_markdown
from pictovap.ecosystem import (
    SUPPORTED_TOOL_KINDS,
    build_ecosystem_match,
    ecosystem_tool_kinds,
    render_ecosystem_markdown,
    render_supported_tool_kinds,
)
from pictovap.plugins import PluginError, iter_plugins
from pictovap.scaffold import ScaffoldError, scaffold_adapter


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _write_text_or_print(rendered: str, output: str | None) -> None:
    if output:
        with open(output, "w", encoding="utf-8") as output_file:
            output_file.write(rendered)
    print(rendered, end="")


def _collect_review_decisions(pack: dict[str, Any], actor: str) -> dict[str, Any]:
    """Prompt for explicit editorial actions; never call providers or a CMS."""
    decisions = list(pack["review"]["decisions"])
    already = {decision["slot_id"] for decision in decisions}
    article = pack["article"]
    print(f"Review article: {article.get('title') or article.get('id')}")
    print("These decisions do not authorize a CMS write or grant image rights.")
    for slot in pack["slots"]:
        slot_id = slot["slot_id"]
        if slot_id in already:
            continue
        proposal = slot["proposal"]
        provenance = proposal.get("provenance") or {}
        print(f"\nSlot: {slot_id} — {slot.get('purpose') or 'image'}")
        print(f"Heading: {slot.get('target_heading') or 'not specified'}")
        print(f"Proposed: {proposal.get('candidate_id') or 'none'}")
        print(f"Observed license: {provenance.get('license_status') or 'unknown'}")
        if provenance.get("source_url"):
            print(f"Source: {provenance['source_url']}")
        if provenance.get("attribution"):
            print(f"Attribution: {provenance['attribution']}")
        for candidate in slot["candidates"]:
            print(
                f"  {candidate.get('candidate_id')}: "
                f"{candidate.get('decision')} / score {candidate.get('final_score', '?')}"
            )
            if candidate.get("human_reason"):
                print(f"    Reason: {candidate['human_reason']}")
        while True:
            choice = input("Choose [a]ccept, [r]eplace, re[j]ect, [q]uit: ").strip().lower()
            if choice == "q":
                raise KeyboardInterrupt
            if choice not in {"a", "r", "j"}:
                print("Choose a, r, j, or q.")
                continue
            action = {"a": "accept", "r": "replace", "j": "reject"}[choice]
            decision: dict[str, Any] = {
                "slot_id": slot_id,
                "action": action,
                "actor": actor,
                "decided_at": datetime.now(timezone.utc).isoformat(),
            }
            if action == "replace":
                replacement_path = input(
                    "Path to existing replacement evidence JSON (candidate_id, provenance, placement): "
                ).strip()
                try:
                    with open(replacement_path, encoding="utf-8") as stream:
                        replacement = json.load(stream)
                    if not isinstance(replacement, dict):
                        raise ValueError("Replacement evidence must be a JSON object")
                    decision["replacement"] = replacement
                except (OSError, ValueError, TypeError) as e:
                    print(f"Invalid replacement evidence: {e}")
                    continue
            try:
                transition_decision_pack_review(pack, decisions + [decision], complete=False)
            except ValueError as e:
                print(f"Decision rejected: {e}")
                continue
            decisions.append(decision)
            break
    return transition_decision_pack_review(pack, decisions, complete=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pictovap")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the installed Pictovap version and exit",
    )
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

    report = sub.add_parser("report", help="Generate an editor-readable report from a plan")
    report.add_argument("--plan", required=True, help="Path to visual-plan.json")
    report.add_argument("--output", required=True, help="Path to write the rendered report")
    report.add_argument("--renderer", help="Installed report-renderer plugin entry-point name")
    report.add_argument("--renderer-option", action="append", default=[], metavar="KEY=VALUE")

    feedback = sub.add_parser(
        "feedback", help="Create an anonymous external-validation summary from a plan"
    )
    feedback.add_argument("--plan", required=True, help="Path to visual-plan.json")
    feedback.add_argument("--output", help="Optional path to write the summary JSON")
    feedback.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format for the anonymous summary",
    )

    validate = sub.add_parser(
        "validate", help="Validate a serialized visual plan without network or CMS access"
    )
    validate.add_argument("--plan", required=True, help="Path to visual-plan.json")
    validate.add_argument(
        "--strict",
        action="store_true",
        help="Treat recommended consistency warnings as validation failures",
    )

    audit = sub.add_parser(
        "audit", help="Audit a visual plan for editorial and integration readiness"
    )
    audit.add_argument("--plan", required=True, help="Path to visual-plan.json")
    audit.add_argument(
        "--format", choices=("json", "markdown"), default="json", help="Output format"
    )
    audit.add_argument(
        "--strict", action="store_true", help="Turn editorial warnings into failures"
    )
    audit.add_argument("--output", help="Optional path to write the audit report")

    benchmark = sub.add_parser(
        "benchmark", help="Run the deterministic golden corpus benchmark without network access"
    )
    benchmark.add_argument("--corpus", required=True, help="Directory containing manifest.yaml and articles")
    benchmark.add_argument(
        "--format", choices=("json", "markdown"), default="json", help="Output format"
    )
    benchmark.add_argument("--output", help="Optional path to write the benchmark receipt")

    registry = sub.add_parser("registry", help="List built-in and installed adapters")
    registry_subcommands = registry.add_subparsers(dest="registry_command", required=True)
    registry_list = registry_subcommands.add_parser(
        "list", help="List adapter metadata without installing or constructing anything"
    )
    registry_list.add_argument("--kind", choices=("provider", "cms", "renderer"), help="Filter by adapter kind")
    registry_list.add_argument(
        "--format", choices=("json", "markdown"), default="json", help="Output format"
    )
    registry_list.add_argument("--output", help="Optional path to write the registry")

    explain = sub.add_parser(
        "explain", help="Explain visual intent, constraints, and candidate decisions from a plan"
    )
    explain.add_argument("--plan", required=True, help="Path to visual-plan.json")
    explain.add_argument(
        "--format", choices=("json", "markdown"), default="markdown", help="Output format"
    )
    explain.add_argument("--output", help="Optional path to write the explanation")

    plan_diff = sub.add_parser(
        "diff", help="Explain changes between two serialized visual plans"
    )
    plan_diff.add_argument("--before", required=True, help="Path to the earlier visual plan")
    plan_diff.add_argument("--after", required=True, help="Path to the later visual plan")
    plan_diff.add_argument(
        "--format", choices=("json", "markdown"), default="markdown", help="Output format"
    )
    plan_diff.add_argument("--output", help="Optional path to write the plan diff")
    plan_diff.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Return exit status 1 when the plans differ, for CI drift gates",
    )

    review = sub.add_parser(
        "review", help="Review visual candidates interactively, without CMS writes"
    )
    review_source = review.add_mutually_exclusive_group(required=True)
    review_source.add_argument("--plan", help="Valid visual plan JSON to review")
    review_source.add_argument("--pack", help="Pending Decision Pack JSON to continue")
    review.add_argument("--actor", required=True, help="Editor identifier for decisions")
    review.add_argument("--output", required=True, help="New JSON file for reviewed Decision Pack")
    review.add_argument("--preview", help="New Markdown file for review preview")

    review_preview = sub.add_parser(
        "review-preview", help="Compare an article proposal with its editor-reviewed pack"
    )
    preview_source = review_preview.add_mutually_exclusive_group(required=True)
    preview_source.add_argument("--plan", help="Original visual plan JSON")
    preview_source.add_argument("--pack", help="Original proposed Decision Pack JSON")
    review_preview.add_argument("--reviewed", required=True, help="Reviewed Decision Pack JSON")
    review_preview.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    review_preview.add_argument("--output", help="Optional comparison report path")

    plugins = sub.add_parser("plugins", help="List installed third-party adapter plugins")
    plugins.add_argument("--kind", choices=("provider", "cms", "renderer"), help="Filter by adapter kind")

    adapter = sub.add_parser("adapter", help="Inspect an installed adapter")
    adapter_subcommands = adapter.add_subparsers(dest="adapter_command", required=True)
    adapter_check = adapter_subcommands.add_parser(
        "check", help="Produce a safe adapter conformance report"
    )
    adapter_check.add_argument("--kind", required=True, choices=("provider", "cms", "renderer"))
    adapter_check.add_argument("--name", required=True, help="Installed adapter entry-point name")
    adapter_check.add_argument("--option", action="append", default=[], metavar="KEY=VALUE")
    adapter_check.add_argument(
        "--exercise", action="store_true",
        help="For providers only: run one bounded search to validate candidate provenance fields",
    )
    adapter_check.add_argument("--query", default="pictovap adapter check")
    adapter_check.add_argument("--count", type=int, default=3)

    scaffold = sub.add_parser("scaffold", help="Generate a standalone adapter plugin package")
    scaffold.add_argument("kind", choices=("provider", "cms"), help="Adapter contract to implement")
    scaffold.add_argument("name", help="Adapter name, for example wikimedia or hugo")
    scaffold.add_argument("--output", default=".", help="Parent directory for the generated package")
    scaffold.add_argument("--force", action="store_true", help="Overwrite scaffold-owned files")

    ecosystem = sub.add_parser(
        "ecosystem",
        help="Generate integration guidance for adjacent publishing tools",
    )
    ecosystem_subcommands = ecosystem.add_subparsers(dest="ecosystem_command", required=True)
    ecosystem_explain = ecosystem_subcommands.add_parser(
        "explain",
        help="List supported adjacent tool categories",
    )
    ecosystem_explain.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format",
    )
    ecosystem_explain.add_argument("--output", help="Optional path to write the rendered output")

    ecosystem_match = ecosystem_subcommands.add_parser(
        "match",
        help="Create a reusable integration packet for an adjacent project",
    )
    ecosystem_match.add_argument(
        "--tool",
        required=True,
        help=f"Adjacent tool kind or alias. Supported values: {', '.join(SUPPORTED_TOOL_KINDS)}",
    )
    ecosystem_match.add_argument("--project-name", default="This project")
    ecosystem_match.add_argument("--repository-url")
    ecosystem_match.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format",
    )
    ecosystem_match.add_argument("--output", help="Optional path to write the rendered output")

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

    if args.command == "review":
        try:
            actor = args.actor.strip()
            if not actor:
                raise ValueError("Editor identifier must not be empty")
            source = Path(args.plan or args.pack).resolve()
            output_path = Path(args.output).resolve()
            preview_path = Path(args.preview).resolve() if args.preview else None
            requested = [output_path] + ([preview_path] if preview_path else [])
            if len(set(requested)) != len(requested) or source in requested:
                raise ValueError("Review input, JSON output and preview paths must be distinct")
            for destination in requested:
                if destination.exists():
                    raise ValueError(f"Refusing to overwrite existing file: {destination}")
            with source.open(encoding="utf-8") as stream:
                payload = json.load(stream)
            pack = build_decision_pack(payload) if args.plan else payload
            if validate_decision_pack(pack)["status"] != "passed":
                raise ValueError("Input Decision Pack did not pass validation")
            if pack["review"]["status"] != "pending":
                raise ValueError("Decision Pack is already reviewed; use review-preview")
            reviewed = _collect_review_decisions(pack, actor)
            comparison = preview_decision_pack(pack, reviewed)
            rendered = render_review_preview(comparison)
            print(rendered, end="")
            created: list[Path] = []
            try:
                with output_path.open("x", encoding="utf-8") as stream:
                    created.append(output_path)
                    json.dump(reviewed, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
                if preview_path:
                    with preview_path.open("x", encoding="utf-8") as stream:
                        created.append(preview_path)
                        stream.write(rendered)
            except OSError:
                for path in created:
                    path.unlink(missing_ok=True)
                raise
            print(f"Reviewed Decision Pack written to {output_path}")
            return 0
        except (OSError, ValueError, TypeError, EOFError, KeyboardInterrupt) as e:
            print(f"Review not saved: {e or 'cancelled'}", file=sys.stderr)
            return 1

    if args.command == "review-preview":
        try:
            with open(args.plan or args.pack, encoding="utf-8") as stream:
                original = json.load(stream)
            with open(args.reviewed, encoding="utf-8") as stream:
                reviewed = json.load(stream)
            pack = build_decision_pack(original) if args.plan else original
            comparison = preview_decision_pack(pack, reviewed)
            rendered = (
                json.dumps(comparison, ensure_ascii=False, indent=2) + "\n"
                if args.format == "json"
                else render_review_preview(comparison)
            )
            if args.output:
                target = Path(args.output).resolve()
                if target in {Path(args.plan or args.pack).resolve(), Path(args.reviewed).resolve()}:
                    raise ValueError("Preview cannot overwrite its source or reviewed pack")
                if target.exists():
                    raise ValueError(f"Refusing to overwrite existing preview: {target}")
                with target.open("x", encoding="utf-8") as stream:
                    stream.write(rendered)
            print(rendered, end="")
            return 0
        except (OSError, TypeError, ValueError) as e:
            print(f"Error previewing editor review: {e}", file=sys.stderr)
            return 1

    if args.command == "publish":
        try:
            result = runner.publish(
                plan=args.plan,
                cms=args.cms,
                cms_options=parse_adapter_options(args.cms_option),
                dry_run=args.dry_run,
            )
            _print_json(result)
            return 0 if result["status"] in {PublishStatus.READY.value, PublishStatus.COMPLETED.value} else 1
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
            return 0 if result["status"] == DoctorStatus.READY.value else 1
        except (RuntimeConfigurationError, PluginError, AdapterConstructionError) as e:
            print(f"Error checking plugins: {e}", file=sys.stderr)
            return 1

    if args.command == "report":
        try:
            renderer = None
            if args.renderer:
                renderer = construct_plugin(
                    "renderer", args.renderer, parse_adapter_options(args.renderer_option)
                )
            elif args.renderer_option:
                raise RuntimeConfigurationError("Renderer options require --renderer")
            generate_report_from_file(args.plan, args.output, renderer=renderer)
            print(f"Report written to {args.output}")
            return 0
        except (RuntimeConfigurationError, PluginError, AdapterConstructionError, OSError, ValueError) as e:
            print(f"Error generating report: {e}", file=sys.stderr)
            return 1

    if args.command == "feedback":
        try:
            with open(args.plan, encoding="utf-8") as plan_file:
                plan_payload = json.load(plan_file)
            summary = summarize_plan(plan_payload)
            if args.format == "markdown":
                rendered = render_feedback_markdown(summary)
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as output_file:
                        output_file.write(rendered)
                print(rendered, end="")
                return 0
            if args.output:
                with open(args.output, "w", encoding="utf-8") as output_file:
                    json.dump(summary, output_file, ensure_ascii=False, indent=2)
                    output_file.write("\n")
            _print_json(summary)
            return 0
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            print(f"Error creating feedback summary: {e}", file=sys.stderr)
            return 1

    if args.command == "validate":
        try:
            with open(args.plan, encoding="utf-8") as plan_file:
                plan_payload = json.load(plan_file)
            from pictovap.validation import validate_visual_plan

            result = validate_visual_plan(plan_payload, strict=args.strict)
            _print_json(result)
            return 0 if result["status"] == "passed" else 1
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            print(f"Error validating plan: {e}", file=sys.stderr)
            return 1

    if args.command == "audit":
        try:
            with open(args.plan, encoding="utf-8") as plan_file:
                plan_payload = json.load(plan_file)
            result = audit_visual_plan(plan_payload, strict=args.strict)
            if args.format == "markdown":
                rendered = render_audit_markdown(result)
                _write_text_or_print(rendered, args.output)
            else:
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as output_file:
                        json.dump(result, output_file, ensure_ascii=False, indent=2)
                        output_file.write("\n")
                _print_json(result)
            return 0 if result["status"] in {"passed", "warning"} else 1
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            print(f"Error auditing plan: {e}", file=sys.stderr)
            return 1

    if args.command == "benchmark":
        try:
            result = run_corpus_benchmark(args.corpus)
            rendered = benchmark_to_json(result) if args.format == "json" else render_benchmark_markdown(result)
            _write_text_or_print(rendered, args.output)
            return 0 if result["status"] == "passed" else 1
        except (OSError, TypeError, ValueError) as e:
            print(f"Error running golden corpus benchmark: {e}", file=sys.stderr)
            return 1

    if args.command == "registry":
        try:
            payload = registry_payload(args.kind)
            rendered = registry_to_json(payload) if args.format == "json" else render_registry_markdown(payload)
            _write_text_or_print(rendered, args.output)
            return 0
        except (OSError, TypeError, ValueError, PluginError) as e:
            print(f"Error listing registry: {e}", file=sys.stderr)
            return 1

    if args.command == "explain":
        try:
            with open(args.plan, encoding="utf-8") as plan_file:
                plan_payload = json.load(plan_file)
            proof = plan_payload.get("intent_proof")
            if not isinstance(proof, dict):
                raise ValueError("Plan does not contain an intent_proof block")
            rendered = intent_proof_to_json(proof) if args.format == "json" else render_intent_markdown(proof)
            _write_text_or_print(rendered, args.output)
            return 0
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            print(f"Error explaining visual plan: {e}", file=sys.stderr)
            return 1

    if args.command == "diff":
        try:
            with open(args.before, encoding="utf-8") as before_file:
                before = json.load(before_file)
            with open(args.after, encoding="utf-8") as after_file:
                after = json.load(after_file)
            result = diff_visual_plans(before, after)
            rendered = (
                plan_diff_to_json(result)
                if args.format == "json"
                else render_plan_diff_markdown(result)
            )
            _write_text_or_print(rendered, args.output)
            return 1 if args.fail_on_change and result["status"] == "changed" else 0
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as e:
            print(f"Error comparing visual plans: {e}", file=sys.stderr)
            return 1

    if args.command == "plugins":
        try:
            _print_json({"plugins": [plugin.to_dict() for plugin in iter_plugins(args.kind)]})
            return 0
        except PluginError as e:
            print(f"Error discovering plugins: {e}", file=sys.stderr)
            return 1

    if args.command == "adapter":
        try:
            result = check_adapter(
                kind=args.kind,
                name=args.name,
                options=parse_adapter_options(args.option),
                exercise=args.exercise,
                query=args.query,
                count=args.count,
            )
            _print_json(result)
            return 0 if result["status"] == "passed" else 1
        except (AdapterCheckError, RuntimeConfigurationError, PluginError, AdapterConstructionError) as e:
            print(f"Error checking adapter: {e}", file=sys.stderr)
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

    if args.command == "ecosystem":
        try:
            if args.ecosystem_command == "explain":
                payload = {"tool_kinds": ecosystem_tool_kinds()}
                if args.format == "markdown":
                    rendered = render_supported_tool_kinds(payload["tool_kinds"])
                    _write_text_or_print(rendered, args.output)
                    return 0
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as output_file:
                        json.dump(payload, output_file, ensure_ascii=False, indent=2)
                        output_file.write("\n")
                _print_json(payload)
                return 0

            if args.ecosystem_command == "match":
                packet = build_ecosystem_match(
                    tool_kind=args.tool,
                    project_name=args.project_name,
                    repository_url=args.repository_url,
                )
                if args.format == "markdown":
                    rendered = render_ecosystem_markdown(packet)
                    _write_text_or_print(rendered, args.output)
                    return 0
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as output_file:
                        json.dump(packet, output_file, ensure_ascii=False, indent=2)
                        output_file.write("\n")
                _print_json(packet)
                return 0
        except (OSError, ValueError) as e:
            print(f"Error creating ecosystem integration packet: {e}", file=sys.stderr)
            return 1

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
