import json
import subprocess
from pathlib import Path


def test_pictovap_demo(tmp_path):
    result = subprocess.run(
        ["pictovap", "demo"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Pictovap Local Demo" in result.stdout


def test_python_m_pictova_demo(tmp_path):
    result = subprocess.run(
        ["python", "-m", "pictovap.demo"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Pictovap Local Demo" in result.stdout
    assert "found in sys.modules" not in result.stderr


def test_pictovap_plan(tmp_path):
    output_json = tmp_path / "output.json"
    result = subprocess.run([
        "pictovap", "plan",
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
        "pictovap", "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json),
        "--report", str(output_md)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert output_json.exists()
    assert output_md.exists()

def test_pictovap_report(tmp_path):
    # First generate a plan
    output_json = tmp_path / "output.json"
    subprocess.run([
        "pictovap", "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json)
    ], check=True)
    
    output_md = tmp_path / "report.md"
    result = subprocess.run([
        "pictovap", "report",
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

def test_pictovap_plan_missing_article(tmp_path):
    output_json = tmp_path / "output.json"
    result = subprocess.run([
        "pictovap", "plan",
        "--article", "missing.md",
        "--profile", "examples/profiles/sample-publisher.yaml",
        "--output", str(output_json)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Error: Article not found" in result.stderr

def test_pictovap_plan_missing_profile(tmp_path):
    output_json = tmp_path / "output.json"
    result = subprocess.run([
        "pictovap", "plan",
        "--article", "examples/articles/travel-guide.md",
        "--profile", "missing.yaml",
        "--output", str(output_json)
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Error: Profile not found" in result.stderr
