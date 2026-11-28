"""Legacy CLI module alias; preserve the old module entry point."""
from importlib import import_module
import sys

if __name__ == "__main__":
    from actovisio_framework.app.cli import legacy_main
    raise SystemExit(legacy_main())
else:
    sys.modules[__name__] = import_module("actovisio_framework.app.cli")
