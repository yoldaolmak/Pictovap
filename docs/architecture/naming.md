# Brand & Naming

## Product Name

**Pictovap** is the public product name. It is used in:
- README and documentation
- GitHub repository name
- PyPI package name
- User-facing descriptions

## Internal Package Name

As of 0.3.0 the importable Python package is `pictovap`, matching the
product and PyPI distribution name. The old `pictova` import name and CLI
command remain as deprecated aliases and emit a `DeprecationWarning`.

| Context | Name | Reason |
|---------|------|--------|
| Product name | Pictovap | Public brand identity |
| Python package | `pictovap` | Renamed in 0.3.0 for consistency |
| Deprecated import alias | `pictova` | Kept for backward compatibility, warns |
| CLI command | `pictovap` (alias: `pictova`) | Consistency; old scripts keep working |
| Repository | `Pictovap` | GitHub repository name |
| PyPI package | `pictovap` | Published package name |

## Etymology

The name derives from Latin *pictus* (past participle of *pingere*, to paint or depict) combined with the suffix *-vap*, suggesting visual automation for publishers.

## Migration

The rename happened in 0.3.0 (see CHANGELOG). Migration is mechanical:
replace `pictova` with `pictovap` in imports. The `pictova` alias will be
removed in a future major version.
