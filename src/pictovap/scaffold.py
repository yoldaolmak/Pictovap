"""Generate standalone, testable Pictovap adapter plugin packages."""

from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent
from typing import Dict, Literal

ScaffoldKind = Literal["provider", "cms"]


class ScaffoldError(ValueError):
    """Raised when a scaffold request is invalid or would overwrite files."""


def _normalize_name(name: str) -> tuple[str, str, str]:
    slug = name.strip().lower().replace("_", "-")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", slug):
        raise ScaffoldError(
            "Adapter name must start with a letter and contain only letters, numbers, or hyphens"
        )
    module = slug.replace("-", "_")
    class_stem = "".join(part.capitalize() for part in module.split("_"))
    return slug, module, class_stem


def _provider_files(slug: str, module: str, class_stem: str) -> Dict[str, str]:
    package = f"pictovap_{module}"
    adapter_class = f"{class_stem}Source"
    return {
        "pyproject.toml": dedent(f'''\
            [build-system]
            requires = ["setuptools>=77"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "pictovap-{slug}"
            version = "0.1.0"
            description = "{class_stem} image-source adapter for Pictovap."
            readme = "README.md"
            requires-python = ">=3.10"
            license = "MIT"
            keywords = ["pictovap", "image adapter", "cms"]
            dependencies = ["pictovap>=0.5.0"]

            [project.entry-points."pictovap.image_sources"]
            {slug} = "{package}:{adapter_class}"

            [project.optional-dependencies]
            test = ["pytest>=9.0.3"]

            [tool.setuptools.packages.find]
            where = ["src"]
        '''),
        f"src/{package}/__init__.py": dedent(f'''\
            """{class_stem} image-source adapter for Pictovap."""

            from __future__ import annotations

            from typing import Any, Dict, List


            class {adapter_class}:
                """Return image candidates from {class_stem}."""

                def __init__(self, api_key: str | None = None) -> None:
                    self.api_key = api_key

                def search_candidates(self, query: str, count: int) -> List[Dict[str, Any]]:
                    # Replace this empty result with the provider API integration.
                    # Missing credentials must remain a safe empty-result path.
                    if not self.api_key:
                        return []
                    return []


            __all__ = ["{adapter_class}"]
        '''),
        "tests/test_adapter.py": dedent(f'''\
            from {package} import {adapter_class}
            from pictovap.testing import assert_image_source_contract


            def test_adapter_contract_without_credentials():
                adapter = {adapter_class}()
                assert assert_image_source_contract(adapter) == []
        '''),
        "README.md": dedent(f'''\
            # pictovap-{slug}

            `{class_stem}` image-source adapter for Pictovap.

            ## Development

            ```bash
            python -m venv .venv
            source .venv/bin/activate
            pip install -e ".[test]"
            pytest
            pictovap plugins --kind provider
            ```

            Implement the provider request in `{adapter_class}.search_candidates`,
            mock all HTTP calls in tests, and preserve the credential-free empty-result path.
        '''),
        ".gitignore": ".venv/\n__pycache__/\n*.egg-info/\n.pytest_cache/\n",
    }


def _cms_files(slug: str, module: str, class_stem: str) -> Dict[str, str]:
    package = f"pictovap_{module}"
    adapter_class = f"{class_stem}Adapter"
    return {
        "pyproject.toml": dedent(f'''\
            [build-system]
            requires = ["setuptools>=77"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "pictovap-{slug}"
            version = "0.1.0"
            description = "{class_stem} CMS adapter for Pictovap."
            readme = "README.md"
            requires-python = ">=3.10"
            license = "MIT"
            keywords = ["pictovap", "cms adapter", "publishing"]
            dependencies = ["pictovap>=0.5.0"]

            [project.entry-points."pictovap.cms"]
            {slug} = "{package}:{adapter_class}"

            [project.optional-dependencies]
            test = ["pytest>=9.0.3"]

            [tool.setuptools.packages.find]
            where = ["src"]
        '''),
        f"src/{package}/__init__.py": dedent(f'''\
            """{class_stem} CMS adapter for Pictovap."""

            from __future__ import annotations

            from typing import Any, Dict

            from pictovap.core.primitives import CMSPlacement


            class {adapter_class}:
                """Place Pictovap image instructions into {class_stem}."""

                def __init__(self, api_url: str, api_token: str) -> None:
                    self.api_url = api_url
                    self.api_token = api_token

                def place(self, placement: CMSPlacement) -> Dict[str, Any]:
                    # Replace this no-op result with the CMS API integration.
                    return {{
                        "placed": [],
                        "failed": [],
                        "warnings": ["Adapter scaffold has no transport implementation"],
                    }}


            __all__ = ["{adapter_class}"]
        '''),
        "tests/test_adapter.py": dedent(f'''\
            from {package} import {adapter_class}
            from pictovap.testing import assert_cms_adapter_contract


            def test_adapter_contract():
                adapter = {adapter_class}("https://cms.example.com", "test-token")
                result = assert_cms_adapter_contract(adapter)
                assert result["warnings"]
        '''),
        "README.md": dedent(f'''\
            # pictovap-{slug}

            `{class_stem}` CMS adapter for Pictovap.

            ## Development

            ```bash
            python -m venv .venv
            source .venv/bin/activate
            pip install -e ".[test]"
            pytest
            pictovap plugins --kind cms
            ```

            Implement the CMS request in `{adapter_class}.place`, mock all HTTP calls
            in tests, and keep the `placed`, `failed`, and `warnings` result fields.
        '''),
        ".gitignore": ".venv/\n__pycache__/\n*.egg-info/\n.pytest_cache/\n",
    }


def scaffold_adapter(
    kind: ScaffoldKind,
    name: str,
    *,
    output: str | Path = ".",
    force: bool = False,
) -> Path:
    """Create a standalone adapter plugin project and return its root path."""
    if kind not in {"provider", "cms"}:
        raise ScaffoldError(f"Unknown adapter kind: {kind}")
    slug, module, class_stem = _normalize_name(name)
    root = Path(output).expanduser().resolve() / f"pictovap-{slug}"
    files = (
        _provider_files(slug, module, class_stem)
        if kind == "provider"
        else _cms_files(slug, module, class_stem)
    )

    conflicts = [str(root / relative) for relative in files if (root / relative).exists()]
    if conflicts and not force:
        raise ScaffoldError(
            "Refusing to overwrite existing scaffold files: " + ", ".join(conflicts)
        )

    for relative, content in files.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    return root


__all__ = ["ScaffoldError", "ScaffoldKind", "scaffold_adapter"]
