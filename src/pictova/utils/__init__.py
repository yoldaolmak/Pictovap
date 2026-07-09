"""
VIL Utils Package - Utility modules for Visual Intelligence Layer

Not: logging_config ve exceptions modülleri henüz oluşturulmadı.
İhtiyaç duyulduğunda ayrı olarak eklenecek.
"""

import logging

__all__ = [
    'get_logger',
    'setup_logging',
]

def get_logger(name: str = 'vil') -> logging.Logger:
    """Basit logger factory."""
    return logging.getLogger(name)

def setup_logging(level: str = 'INFO', json_format: bool = False):
    """Basit logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=fmt)
