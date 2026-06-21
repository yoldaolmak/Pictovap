from pathlib import Path
import os
import sys

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_main_import():
    import src.main  # noqa: F401


def test_visual_memory_exports():
    from src.visual_memory import VisualMemoryComponent, VisualMemoryConfig

    config = VisualMemoryConfig(database_path=Path(":memory:"))
    component = VisualMemoryComponent(config)
    assert component is not None


def test_processor_filter_path():
    from src.core.processor import YOImageProcessor

    image = Image.new("RGB", (8, 8), "white")
    os.environ["YO_IMAGE_FILTER_PROFILE"] = "yoldaolmak"
    filtered, details = YOImageProcessor().apply_yo_filter(image)
    assert filtered.size == image.size
    assert "profile" in details


def test_config_uses_repo_root_defaults():
    from src.utils.config import PROJECT_ROOT, get_visual_memory_db_path, get_vil_dir

    assert PROJECT_ROOT == REPO_ROOT
    assert isinstance(get_visual_memory_db_path(), Path)
    assert isinstance(get_vil_dir(), Path)


def test_wordpress_module_import():
    import src.services.wordpress  # noqa: F401
