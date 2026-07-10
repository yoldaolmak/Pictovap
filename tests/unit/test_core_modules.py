from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_config_visual_memory_db_path_is_a_path():
    from pictova.utils.config import PROJECT_ROOT, get_visual_memory_db_path

    # PROJECT_ROOT is computed from utils/config.py's own installed
    # location, so it only equals the source checkout root in a dev/editable
    # install — for a real `pip install pictovap`, it resolves to some
    # site-packages-relative directory instead. That's fine: it only backs
    # a fully optional, gracefully-degrading local DB lookup (see
    # `_lookup_indexed_asset_context` in metadata_generator.py), so this test
    # only checks the type, not equality with the checkout root.
    assert isinstance(PROJECT_ROOT, Path)
    assert isinstance(get_visual_memory_db_path(), Path)


def test_config_vil_dir_has_no_personal_machine_default(monkeypatch):
    """get_vil_dir() must never default to a path specific to any one
    contributor's machine — it should degrade to None when YO_VIL_DIR is
    unset, matching the env_str() graceful-degradation pattern."""
    monkeypatch.delenv("YO_VIL_DIR", raising=False)
    from pictova.utils.config import get_vil_dir

    assert get_vil_dir() is None


def test_config_vil_dir_honors_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("YO_VIL_DIR", str(tmp_path / "custom-vil"))
    from pictova.utils.config import get_vil_dir

    assert get_vil_dir() == tmp_path / "custom-vil"


def test_wordpress_module_import():
    import pictova.services.wordpress  # noqa: F401
