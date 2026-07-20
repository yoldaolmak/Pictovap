import json
import subprocess
import sys
from pathlib import Path

from pictovap import __version__
from pictovap.app import cli
from pictovap.services.wordpress import WordPressPostReadError


PICTOVAP = str(Path(sys.executable).with_name("pictovap"))


def test_pictovap_demo(tmp_path):
    result = subprocess.run(
        [PICTOVAP, "demo"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Pictovap Local Demo" in result.stdout


def test_pictovap_version_matches_installed_package_version():
    result = subprocess.run([PICTOVAP, "--version"], capture_output=True, text=True)

    assert result.returncode == 0
    assert result.stdout.strip() == f"pictovap {__version__}"


def test_python_m_pictova_demo(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "pictovap.demo"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Pictovap Local Demo" in result.stdout
    assert "found in sys.modules" not in result.stderr


def test_pictovap_plan(tmp_path):
    output_json = tmp_path / "output.json"
    result = subprocess.run([
        PICTOVAP, "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert output_json.exists()
    
    with open(output_json) as f:
        data = json.load(f)
        assert "visual_brief" in data
        assert "fit_scores" in data
        assert "provenance_packs" in data
        assert "cms_placement" in data
        assert "source_path" in data

def test_pictovap_plan_with_report(tmp_path):
    output_json = tmp_path / "output.json"
    output_md = tmp_path / "output.md"
    result = subprocess.run([
        PICTOVAP, "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json),
        "--report", str(output_md)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert output_json.exists()
    assert output_md.exists()


def test_plan_rejects_article_and_wordpress_post_together():
    result = subprocess.run([
        PICTOVAP, "plan", "--article", "examples/articles/travel-guide.md",
        "--wordpress-post", "42",
    ], capture_output=True, text=True)

    assert result.returncode != 0
    assert "not allowed with argument" in result.stderr


def test_plan_dispatches_wordpress_post_without_network(monkeypatch, capsys):
    calls = []

    def fake_plan_wordpress_post(self, **kwargs):
        calls.append(kwargs)
        return {"source_path": f"wordpress://{kwargs['site']}/posts/{kwargs['post_id']}"}

    monkeypatch.setattr(cli.PipelineRunner, "plan_wordpress_post", fake_plan_wordpress_post)

    result = cli.main([
        "plan",
        "--wordpress-post",
        "42",
        "--wordpress-site",
        "publisher",
    ])

    assert result == 0
    assert calls == [{
        "post_id": 42,
        "site": "publisher",
        "profile": None,
        "output": None,
        "report": None,
        "provider": None,
        "provider_options": {},
    }]
    assert json.loads(capsys.readouterr().out) == {
        "source_path": "wordpress://publisher/posts/42"
    }


def test_plan_reports_safe_wordpress_read_error(monkeypatch, capsys):
    def fail_plan_wordpress_post(self, **kwargs):
        raise WordPressPostReadError("WordPress post 42 could not be read: permission denied (HTTP 403)")

    monkeypatch.setattr(cli.PipelineRunner, "plan_wordpress_post", fail_plan_wordpress_post)

    result = cli.main([
        "plan",
        "--wordpress-post",
        "42",
        "--wordpress-site",
        "publisher",
    ])

    captured = capsys.readouterr()
    assert result == 1
    assert captured.out == ""
    assert captured.err == (
        "Error running plan: WordPress post 42 could not be read: "
        "permission denied (HTTP 403)\n"
    )


def test_pictovap_report(tmp_path):
    # First generate a plan
    output_json = tmp_path / "output.json"
    subprocess.run([
        PICTOVAP, "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json)
    ], check=True)
    
    output_md = tmp_path / "report.md"
    result = subprocess.run([
        PICTOVAP, "report",
        "--plan", str(output_json),
        "--output", str(output_md)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert output_md.exists()
    
    content = output_md.read_text(encoding="utf-8")
    assert "# Pictovap Visual Plan" in content
    assert "## Article" in content
    assert "## Visual Brief" in content
    assert "## Selected Images" in content
    assert "## Candidates Requiring Review" in content
    assert "## Provenance" in content
    assert "## CMS Placement Plan" in content
    assert "## Editorial Review Checklist" in content
    # report is not raw json
    assert not content.strip().startswith("{")


def test_report_dispatches_installed_renderer(monkeypatch, tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}", encoding="utf-8")
    output_path = tmp_path / "report.html"
    renderer = object()
    calls = []

    monkeypatch.setattr(cli, "construct_plugin", lambda kind, name, options: renderer)
    monkeypatch.setattr(
        cli,
        "generate_report_from_file",
        lambda plan, output, renderer=None: calls.append((plan, output, renderer)),
    )

    assert cli.main([
        "report", "--plan", str(plan_path), "--output", str(output_path),
        "--renderer", "html-review", "--renderer-option", "theme=light",
    ]) == 0
    assert calls == [(str(plan_path), str(output_path), renderer)]

def test_pictovap_plan_missing_article(tmp_path):
    output_json = tmp_path / "output.json"
    result = subprocess.run([
        PICTOVAP, "plan",
        "--article", "missing.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Error: Article not found" in result.stderr

def test_pictovap_plan_missing_profile(tmp_path):
    output_json = tmp_path / "output.json"
    result = subprocess.run([
        PICTOVAP, "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "missing.yaml",
        "--output", str(output_json)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Error: Profile not found" in result.stderr
