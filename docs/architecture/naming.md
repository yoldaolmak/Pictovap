# Brand & Naming

## Canonical identity (0.14.0)

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

The canonical `actovisio-framework` 0.14.0 distribution is published. See
[Release status](../release-status.md). The canonical wheel owns only its new
namespace; a separately built legacy wheel owns only the old namespace and
requires the exact canonical version. Old `pictovap` 0.13.0 remains immutable,
and publishing the matching `pictovap` 0.14.0 compatibility wheel requires its
own trusted-publisher gate.

Stable wire/schema kind names, entry-point groups, existing environment names,
historical producer identity, MIT notices and attribution are not renamed.
[API Stability](../../API_STABILITY.md) governs compatibility. Product adoption
requires a separately accepted released dependency and replay tests.
