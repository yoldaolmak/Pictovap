"""Test actual wheels in a clean environment, without publishing either distribution."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path


def run(*args, cwd):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE).stdout


def one_wheel(directory):
    wheels = list(Path(directory).resolve().glob("*.whl"))
    assert len(wheels) == 1, wheels
    return wheels[0]


def main():
    canonical, legacy = map(one_wheel, sys.argv[1:])
    with zipfile.ZipFile(canonical) as wheel:
        names = wheel.namelist()
        assert any(n.startswith("actovisio_framework/") for n in names)
        assert not any(n.startswith("pictovap/") for n in names)
        assert any(n.endswith("/licenses/LICENSE") for n in names)
    with zipfile.ZipFile(legacy) as wheel:
        names = wheel.namelist()
        assert any(n.startswith("pictovap/") for n in names)
        assert not any(n.startswith("actovisio_framework/") for n in names)
        assert any(n.endswith("/licenses/LICENSE") for n in names)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = root / "venv"
        venv.EnvBuilder(with_pip=True).create(env)
        python = env / "bin" / "python"
        new_cli = env / "bin" / "actovisio-framework"
        old_cli = env / "bin" / "pictovap"
        run(python, "-m", "pip", "install", canonical, cwd=root)
        run(python, "-c", "from importlib.util import find_spec; "
            "from importlib.metadata import version; "
            "from actovisio_framework import sample_visual_plan, build_decision_pack, validate_decision_pack; "
            "assert find_spec('pictovap') is None; "
            "assert version('actovisio-framework') == '0.14.0'; "
            "assert validate_decision_pack(build_decision_pack(sample_visual_plan()))['status'] == 'passed'", cwd=root)
        assert run(new_cli, "--version", cwd=root).strip() == "actovisio-framework 0.14.0"
        assert "ActoVisio Framework Local Demo" in run(new_cli, "demo", cwd=root)
        assert run(python, "-m", "actovisio_framework", "--version", cwd=root).strip() == "actovisio-framework 0.14.0"
        # Existing released users can coexist before upgrading, with distinct
        # namespaces; the legacy shim is installed only after canonical.
        run(python, "-m", "pip", "install", "pictovap==0.13.0", cwd=root)
        run(python, "-c", "from importlib.metadata import version; "
            "assert version('pictovap') == '0.13.0'; "
            "assert version('actovisio-framework') == '0.14.0'", cwd=root)
        run(python, "-c", "import json; from pathlib import Path; "
            "from pictovap import sample_visual_plan, build_decision_pack; "
            "Path('historical-pack.json').write_text(json.dumps(build_decision_pack(sample_visual_plan())))", cwd=root)
        run(python, "-m", "pip", "install", legacy, cwd=root)
        run(python, "-m", "pip", "check", cwd=root)
        run(python, "-c", "import json, importlib; from pathlib import Path; "
            "from importlib.metadata import version; from importlib.resources import files; "
            "import pictovap as old; import actovisio_framework as new; "
            "assert version('pictovap') == version('actovisio-framework') == '0.14.0'; "
            "assert old.build_decision_pack is new.build_decision_pack; "
            "assert importlib.import_module('pictovap.core.adapters') is "
            "importlib.import_module('actovisio_framework.core.adapters'); "
            "assert files('pictovap.schemas').joinpath('publisher-profile-v1.schema.json').read_bytes() == "
            "files('actovisio_framework.schemas').joinpath('publisher-profile-v1.schema.json').read_bytes(); "
            "pack = json.loads(Path('historical-pack.json').read_text()); "
            "assert new.validate_decision_pack(pack)['status'] == 'passed'; "
            "assert new.build_decision_pack(new.sample_visual_plan()) == "
            "old.build_decision_pack(old.sample_visual_plan())", cwd=root)
        assert run(old_cli, "--version", cwd=root).strip() == "pictovap 0.14.0"
        assert run(python, "-m", "pictovap", "--version", cwd=root).strip() == "pictovap 0.14.0"
        assert "ActoVisio Framework Local Demo" in run(old_cli, "demo", cwd=root)
        # Removing legacy compatibility must not delete canonical files.
        run(python, "-m", "pip", "uninstall", "-y", "pictovap", cwd=root)
        assert run(new_cli, "--version", cwd=root).strip() == "actovisio-framework 0.14.0"
        print("Canonical wheel, legacy upgrade, historical pack and uninstall isolation passed.")


if __name__ == "__main__":
    main()
