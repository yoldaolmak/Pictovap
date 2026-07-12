"""Deprecated import alias for the renamed ``pictovap`` package.

The importable package was renamed from ``pictova`` to ``pictovap`` in
0.3.0 to match the product and PyPI distribution name (see
docs/architecture/naming.md). This shim keeps old imports working:

    import pictova                      # works, warns
    from pictova import create_visual_plan
    from pictova.core.primitives import VisualBrief

Every aliased name resolves to the *same* module object as its
``pictovap`` counterpart, so ``isinstance`` checks and module-level state
stay consistent across both spellings. New code should import
``pictovap`` directly; this alias will be removed in a future major
version.
"""

import importlib
import pkgutil
import sys
import warnings

import pictovap

warnings.warn(
    "The 'pictova' package name is deprecated; it was renamed to "
    "'pictovap' in 0.3.0. Update your imports to 'pictovap'.",
    DeprecationWarning,
    stacklevel=2,
)

_NEW = pictovap.__name__
_OLD = "pictova"

for _info in pkgutil.walk_packages(pictovap.__path__, prefix=_NEW + "."):
    try:
        importlib.import_module(_info.name)
    except Exception:
        # An unimportable submodule must not break the alias shim; it will
        # raise its real error if imported directly.
        continue

for _name, _module in list(sys.modules.items()):
    if _name == _NEW or _name.startswith(_NEW + "."):
        sys.modules[_OLD + _name[len(_NEW):]] = _module
