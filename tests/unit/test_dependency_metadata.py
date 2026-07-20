"""Guards for the published package's supported runtime surface."""

from importlib.metadata import metadata, requires


def test_supported_python_floor_matches_security_baseline():
    assert metadata("pictovap")["Requires-Python"] == ">=3.10"


def test_runtime_dependencies_are_minimal_and_security_fixed():
    declared = requires("pictovap") or []
    runtime = {requirement.lower() for requirement in declared if "extra ==" not in requirement}

    assert runtime == {
        "pillow>=12.3.0",
        "pyyaml>=6.0.2",
        "requests>=2.33.0",
    }
