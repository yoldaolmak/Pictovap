**Title:** Add license confidence mapping to Provenance Pack
**Type:** Feature request
**Labels:** `enhancement`, `good first issue`, `core`

**Problem:**
Different image APIs return licenses in different string formats (e.g., `"cc0"`, `"CC0 1.0"`, `"creative_commons"`, `"unsplash"`). Pictovap currently passes these as raw strings. A unified `LicenseType` enum would make license handling more reliable and auditable.

**Why it matters:** 
License handling is safety-critical for publishers. A unified enum reduces the risk of misclassified licenses and makes the Provenance Pack more trustworthy as an audit trail.

**Proposed approach:**
- Define a `LicenseType` enum in `src/pictovap/core/primitives.py`.
- Map common license strings from supported providers to the enum.
- Update the Provenance Pack to use `LicenseType` instead of raw strings.
- Add unit tests for mapping edge cases.

**Acceptance criteria:**
- `LicenseType` enum covers at least: `CC0`, `CC_BY`, `CC_BY_SA`, `CC_BY_NC`, `UNSPLASH`, `EDITORIAL`, `UNKNOWN`.
- Existing providers map their license strings to the enum.
- Provenance Pack stores the enum value.
- Unit tests cover known license string variants.

**Credentials required:** No
**Difficulty:** Low
