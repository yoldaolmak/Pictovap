"""Legacy import namespace; implementation lives in ActoVisio Framework."""
from importlib import import_module

_target = import_module("actovisio_framework.core")
__all__ = getattr(_target, "__all__", [name for name in vars(_target) if not name.startswith("_")])


def __getattr__(name):
    return getattr(_target, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_target)))
