from __future__ import annotations

import subprocess
import sys

import pytest

from pictovap.scaffold import ScaffoldError, scaffold_adapter


@pytest.mark.parametrize("kind,group,class_name", [
    ("provider", "pictovap.image_sources", "WikimediaSource"),
    ("cms", "pictovap.cms", "HugoAdapter"),
])
def test_scaffold_generates_installable_src_layout(tmp_path, kind, group, class_name):
    name = "wikimedia" if kind == "provider" else "hugo"

    root = scaffold_adapter(kind, name, output=tmp_path)

    assert root == tmp_path / f"pictovap-{name}"
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    source = next((root / "src").glob("*/__init__.py")).read_text(encoding="utf-8")
    assert group in pyproject
    assert "pictovap>=0.6.0" in pyproject
    assert class_name in source
    assert "__test__ = False" in source
    if kind == "provider":
        assert "def search_candidates(\n" in source
    assert (root / "tests/test_adapter.py").exists()
    assert (root / "README.md").exists()
    contributing = (root / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "First successful loop" in contributing
    assert "Definition of done" in contributing


def test_scaffold_refuses_to_overwrite_owned_files(tmp_path):
    scaffold_adapter("provider", "wikimedia", output=tmp_path)

    with pytest.raises(ScaffoldError, match="Refusing to overwrite"):
        scaffold_adapter("provider", "wikimedia", output=tmp_path)


def test_scaffold_force_updates_owned_files(tmp_path):
    root = scaffold_adapter("provider", "wikimedia", output=tmp_path)
    readme = root / "README.md"
    readme.write_text("changed", encoding="utf-8")

    scaffold_adapter("provider", "wikimedia", output=tmp_path, force=True)

    assert readme.read_text(encoding="utf-8").startswith("# pictovap-wikimedia")


@pytest.mark.parametrize("name", ["", "123", "bad name", "../escape"])
def test_scaffold_rejects_unsafe_names(tmp_path, name):
    with pytest.raises(ScaffoldError):
        scaffold_adapter("provider", name, output=tmp_path)


def test_scaffold_cli_prints_created_directory(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pictovap.app.cli",
            "scaffold",
            "provider",
            "wikimedia",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == str(tmp_path / "pictovap-wikimedia")


def test_plugins_cli_returns_machine_readable_json():
    result = subprocess.run(
        [sys.executable, "-m", "pictovap.app.cli", "plugins", "--kind", "provider"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip().startswith('{\n  "plugins":')
