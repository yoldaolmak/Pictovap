from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_workspace_root_defaults_to_cwd(monkeypatch, tmp_path):
    """Runtime files must resolve relative to the user's working directory,
    never the package installation directory — for a real
    `pip install pictovap`, module-relative paths land inside site-packages,
    which is unwritable and wrong (a past release-blocking bug class)."""
    monkeypatch.delenv("PICTOVA_WORKSPACE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    from pictovap.utils.config import get_workspace_root

    assert get_workspace_root() == tmp_path


def test_workspace_root_honors_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("PICTOVA_WORKSPACE_DIR", str(tmp_path / "workspace"))
    from pictovap.utils.config import get_workspace_root

    assert get_workspace_root() == tmp_path / "workspace"


def test_manifest_dir_is_under_workspace_root(monkeypatch, tmp_path):
    monkeypatch.delenv("PICTOVA_POST_MANIFEST_DIR", raising=False)
    monkeypatch.setenv("PICTOVA_WORKSPACE_DIR", str(tmp_path))
    from pictovap.services.post_media_guard import get_manifest_dir

    assert get_manifest_dir() == tmp_path / "data" / "post_media_manifests"


def test_config_vil_dir_has_no_personal_machine_default(monkeypatch):
    """get_vil_dir() must never default to a path specific to any one
    contributor's machine — it should degrade to None when YO_VIL_DIR is
    unset, matching the env_str() graceful-degradation pattern."""
    monkeypatch.delenv("YO_VIL_DIR", raising=False)
    from pictovap.utils.config import get_vil_dir

    assert get_vil_dir() is None


def test_config_vil_dir_honors_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("YO_VIL_DIR", str(tmp_path / "custom-vil"))
    from pictovap.utils.config import get_vil_dir

    assert get_vil_dir() == tmp_path / "custom-vil"


def test_wordpress_module_import():
    import pictovap.services.wordpress  # noqa: F401


def test_package_version_matches_pyproject():
    """pictovap.__version__ must stay in sync with pyproject.toml — it
    drifted once (package said 0.2.0 while pyproject said 0.2.1)."""
    import re

    import pictovap

    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, flags=re.M)
    assert match is not None, "version not found in pyproject.toml"
    assert pictovap.__version__ == match.group(1)
