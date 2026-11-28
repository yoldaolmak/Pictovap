"""Legacy module alias; no second implementation."""
from importlib import import_module
import sys

if __name__ == "__main__":
    import runpy
    runpy.run_module("actovisio_framework.registry", run_name="__main__")
else:
    sys.modules[__name__] = import_module("actovisio_framework.registry")
