"""Utility modules shared across the Pictovap pipeline."""

import logging

__all__ = [
    'get_logger',
    'setup_logging',
]


def get_logger(name: str = 'pictovap') -> logging.Logger:
    """Simple logger factory."""
    return logging.getLogger(name)


def setup_logging(level: str = 'INFO', json_format: bool = False):
    """Simple logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=fmt)
