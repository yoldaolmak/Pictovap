"""The pictova → pictovap rename (0.3.0) must keep old imports working
through the deprecation alias shim, resolving to the same module objects."""

import sys
import warnings


def test_old_name_imports_with_deprecation_warning():
    for name in [m for m in list(sys.modules) if m == "pictova" or m.startswith("pictova.")]:
        del sys.modules[name]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        import pictova  # noqa: F401

    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_old_and_new_names_are_the_same_modules():
    import pictova
    import pictovap

    assert pictova is pictovap

    from pictova.core.primitives import VisualBrief as OldBrief
    from pictovap.core.primitives import VisualBrief as NewBrief

    assert OldBrief is NewBrief


def test_public_api_reachable_through_old_name():
    import pictova

    assert pictova.__version__
    assert callable(pictova.create_visual_plan)
