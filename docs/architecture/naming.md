# Brand & Naming

## Canonical identity (0.14.0 candidate)

ActoVisio Framework is the public MIT framework, formerly Pictovap Framework.
It retains repository ID 1294864094. The private ActoVisio application and
Pictova remain separate.

| Context | Canonical | Legacy compatibility |
| --- | --- | --- |
| Display brand | ActoVisio Framework | Pictovap Framework (historical) |
| Repository | `ActoVisio-Framework` | GitHub redirects old repository |
| PyPI | `actovisio-framework` | `pictovap` |
| Python import | `actovisio_framework` | `pictovap` |
| CLI | `actovisio-framework` | `pictovap` |

The candidate is not published. See [Release status](../release-status.md).
The canonical wheel owns only its new namespace; a separately built legacy
wheel owns only the old namespace and requires the exact canonical version.
Old 0.13.0 remains immutable. Publish and verify the canonical wheel first;
only then consider publishing its matching legacy compatibility wheel.

Stable wire/schema kind names, entry-point groups, existing environment names,
historical producer identity, MIT notices and attribution are not renamed.
[API Stability](../../API_STABILITY.md) governs compatibility. Product adoption
requires a separately accepted released dependency and replay tests.
