# Pictovap compatibility distribution

This optional migration package contains no independent planning implementation.
It depends on the exact matching ActoVisio Framework release and forwards the
legacy Python module and CLI names. It owns the legacy namespace; the canonical
wheel owns only `actovisio_framework`. Existing releases remain available.

Use `actovisio-framework` for new installations. Upgrade the legacy package
only after the matching canonical release is published and verified. Schema and
plugin entry-point identifiers are retained for compatibility. Both packages
remain MIT licensed. This source checkout is not a claim of PyPI publication.
