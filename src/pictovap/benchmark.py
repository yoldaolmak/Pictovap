"""Deterministic golden-corpus benchmark for the public planning pipeline.

The benchmark deliberately uses a synthetic, credential-free image source. It
exercises the same public API that an external adapter uses, while keeping CI
reproducible and offline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from pictovap.api import create_visual_plan
from pictovap.testing.contracts import sample_candidate
from pictovap.validation import validate_visual_plan


class _GoldenCorpusProvider:
    """Return stable candidates without network access or credentials."""

    def __init__(self, prefix: str, candidate_count: int) -> None:
        self.prefix = prefix
        self.candidate_count = candidate_count

    def search_candidates(self, query: str, count: int) -> list[dict[str, Any]]:
        query_keywords = [word.lower() for word in query.split() if word.isalpha()]
        total = max(count, self.candidate_count)
        return [
            {
                **sample_candidate(f"{self.prefix}-{index}"),
                "filename": f"{self.prefix}-{index}.webp",
                "provider": "golden-corpus",
                "source_type": "url",
                "source_url": f"https://images.example.test/{self.prefix}-{index}.webp",
                "keywords": ["article", "guide", "content", "image", *query_keywords],
            }
            for index in range(total)
        ][:count]


def _manifest_path(corpus: str | Path) -> Path:
    root = Path(corpus)
    return root / "manifest.yaml" if root.is_dir() else root


def _load_manifest(corpus: str | Path) -> tuple[Path, list[Mapping[str, Any]]]:
    manifest = _manifest_path(corpus).resolve()
    if not manifest.exists():
        raise FileNotFoundError(f"Golden corpus manifest not found: {manifest}")
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or payload.get("schema_version") != 1:
        raise ValueError("Golden corpus manifest must declare schema_version: 1")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Golden corpus manifest must contain a non-empty cases list")
    if not all(isinstance(case, Mapping) for case in cases):
        raise ValueError("Each golden corpus case must be a mapping")
    return manifest.parent, cases


def _case_result(case: Mapping[str, Any], corpus_root: Path) -> dict[str, Any]:
    case_id = str(case.get("id", ""))
    article_name = case.get("article")
    expected = case.get("expected")
    if not case_id or not isinstance(article_name, str) or not isinstance(expected, Mapping):
        raise ValueError(f"Case {case_id or '<unknown>'} must define id, article, and expected")

    article = (corpus_root / article_name).resolve()
    if corpus_root not in article.parents or not article.exists():
        raise FileNotFoundError(f"Corpus article not found inside corpus: {article_name}")

    expected_language = str(expected.get("language", "en"))
    expected_slots = int(expected.get("slots", 0))
    expected_placements = int(expected.get("placements", expected_slots))
    expected_captions = int(expected.get("captions", expected_placements))
    provider = _GoldenCorpusProvider(case_id, max(expected_slots, expected_placements, 1))
    plan = create_visual_plan(str(article), provider_adapter=provider, provider_name="golden-corpus")

    placements = plan.get("cms_placement", {}).get("placements", [])
    provenance = plan.get("provenance_packs", [])
    captions = sum(bool(item.get("caption")) for item in placements if isinstance(item, Mapping))
    validation = validate_visual_plan(plan, strict=True)
    checks = {
        "language": plan.get("visual_brief", {}).get("article_language") == expected_language,
        "slots": len(plan.get("visual_brief", {}).get("image_slots", [])) == expected_slots,
        "placements": len(placements) == expected_placements,
        "captions": captions == expected_captions,
        "provenance": len(provenance) == expected_placements,
        "validation": validation["status"] == "passed",
    }
    errors = [name for name, passed in checks.items() if not passed]
    return {
        "id": case_id,
        "status": "passed" if not errors else "failed",
        "checks": checks,
        "actual": {
            "language": plan.get("visual_brief", {}).get("article_language"),
            "slots": len(plan.get("visual_brief", {}).get("image_slots", [])),
            "placements": len(placements),
            "captions": captions,
            "provenance": len(provenance),
        },
        "errors": errors,
    }


def run_corpus_benchmark(corpus: str | Path) -> dict[str, Any]:
    """Run every manifest case and return a JSON-safe benchmark receipt."""
    root, cases = _load_manifest(corpus)
    results: list[dict[str, Any]] = []
    for case in cases:
        try:
            results.append(_case_result(case, root))
        except (FileNotFoundError, TypeError, ValueError, KeyError) as exc:
            results.append({
                "id": str(case.get("id", "<unknown>")),
                "status": "failed",
                "checks": {},
                "actual": {},
                "errors": [str(exc)],
            })
    passed = sum(item["status"] == "passed" for item in results)
    failed = len(results) - passed
    return {
        "schema_version": "1",
        "status": "passed" if failed == 0 else "failed",
        "corpus": {"name": root.name, "cases": len(results)},
        "cases": results,
        "summary": {"passed": passed, "failed": failed},
    }


def render_benchmark_markdown(result: Mapping[str, Any]) -> str:
    """Render a compact benchmark receipt for pull requests and CI logs."""
    summary = result.get("summary", {})
    lines = [
        "# Golden Corpus Benchmark",
        "",
        f"**Status:** `{result.get('status', 'failed')}`  ",
        f"**Cases:** {summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed",
        "",
        "| Case | Status | Checks |",
        "| --- | --- | --- |",
    ]
    for case in result.get("cases", []):
        checks = case.get("checks", {})
        passed = sum(bool(value) for value in checks.values())
        lines.append(f"| `{case.get('id', '<unknown>')}` | `{case.get('status', 'failed')}` | {passed}/{len(checks)} |")
    lines.extend(["", "This benchmark uses synthetic candidates and never calls a provider or CMS.", ""])
    return "\n".join(lines)


def benchmark_to_json(result: Mapping[str, Any]) -> str:
    """Serialize a benchmark receipt with stable formatting."""
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


__all__ = ["benchmark_to_json", "render_benchmark_markdown", "run_corpus_benchmark"]
