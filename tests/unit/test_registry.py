import json
import subprocess
import sys

from pictovap.registry import registry_payload, render_registry_markdown


def test_registry_lists_builtin_adapters_without_constructing_them():
    payload = registry_payload()

    assert payload["status"] == "ready"
    assert payload["read_only"] is True
    assert payload["summary"] == {"total": 10, "builtin": 10, "plugins": 0}
    names = {(entry["kind"], entry["name"]) for entry in payload["entries"]}
    assert ("provider", "openverse") in names
    assert ("cms", "wordpress") in names
    assert ("renderer", "markdown") in names


def test_registry_markdown_explains_safe_discovery():
    rendered = render_registry_markdown(registry_payload("provider"))

    assert "# Pictovap Registry" in rendered
    assert "`provider`" in rendered
    assert "never installs packages" in rendered


def test_registry_cli_emits_filtered_json(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "pictovap", "registry", "list", "--kind", "cms"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["total"] == 3
    assert {entry["name"] for entry in payload["entries"]} == {"ghost", "strapi", "wordpress"}
