import json
import subprocess
import sys
from pathlib import Path

from pictovap.benchmark import render_benchmark_markdown, run_corpus_benchmark


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS = REPO_ROOT / "tests" / "corpus"


def test_golden_corpus_benchmark_passes_all_cases():
    result = run_corpus_benchmark(CORPUS)

    assert result["status"] == "passed"
    assert result["summary"] == {"passed": 6, "failed": 0}
    assert all(case["status"] == "passed" for case in result["cases"])


def test_golden_corpus_markdown_is_reviewer_friendly():
    rendered = render_benchmark_markdown(run_corpus_benchmark(CORPUS))

    assert "# Golden Corpus Benchmark" in rendered
    assert "| `travel` | `passed` | 7/7 |" in rendered
    assert "never calls a provider or CMS" in rendered


def test_benchmark_reports_invalid_case_without_aborting(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.yaml").write_text(
        "schema_version: 1\ncases:\n  - id: broken\n    article: missing.md\n    expected: {}\n",
        encoding="utf-8",
    )

    result = run_corpus_benchmark(corpus)

    assert result["status"] == "failed"
    assert result["summary"] == {"passed": 0, "failed": 1}
    assert result["cases"][0]["id"] == "broken"
    assert "not found" in result["cases"][0]["errors"][0]


def test_benchmark_cli_emits_json_and_exit_success(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "pictovap", "benchmark", "--corpus", str(CORPUS)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "passed"
    assert payload["summary"]["passed"] == 6
