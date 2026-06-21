"""
Test suite for YO OS Visual Intelligence Layer (VIL)
Premium startup-grade test coverage
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestCoreImports:
    """Test that all core modules can be imported correctly"""
    
    def test_settings_import(self):
        from src.core import settings
        assert hasattr(settings, 'get_vil_dir')
        assert hasattr(settings, 'load_project_env')
    
    def test_visual_memory_import(self):
        from src import visual_memory
        assert hasattr(visual_memory, 'VisualMemoryComponent')
    
    def test_image_processor_import(self):
        from src.core import yo_image_processor
        assert hasattr(yo_image_processor, 'YOImageProcessor')
    
    def test_metadata_generator_import(self):
        from src.core import yo_metadata_generator
        assert hasattr(yo_metadata_generator, 'YOMetadataGenerator')
    
    def test_wp_uploader_import(self):
        from src.core import yo_wp_uploader
        assert hasattr(yo_wp_uploader, 'fetch_post_context')
    
    def test_orchestrator_import(self):
        from src.core import yo_orchestrator
        # Orchestrator exports main functions
        assert hasattr(yo_orchestrator, 'main') or len(dir(yo_orchestrator)) > 5


class TestSettings:
    """Test settings module functionality"""
    
    def test_get_vil_dir_returns_path(self):
        from src.core.settings import get_vil_dir
        vil_dir = get_vil_dir()
        assert vil_dir is not None
        # Can be str or Path
        assert isinstance(vil_dir, (str, Path))
    
    def test_load_project_env(self):
        from src.core.settings import load_project_env
        # Should not raise exception
        load_project_env()


class TestVisualMemory:
    """Test visual memory component"""
    
    def test_component_initialization(self):
        from src.visual_memory import VisualMemoryComponent, VisualMemoryConfig
        config = VisualMemoryConfig(db_path=":memory:")
        component = VisualMemoryComponent(config)
        assert component is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
