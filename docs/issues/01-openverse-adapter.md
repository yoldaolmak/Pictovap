**Title:** Add Openverse image source adapter
**Type:** Feature request
**Labels:** `enhancement`, `good first issue`, `adapter`

**Problem:**
Pictovap currently supports Unsplash, DepositPhotos (stub), and a local visual memory database as image sources. Openverse is a large, free, CC-licensed image search API maintained by WordPress.org that would expand the candidate pool significantly.

**Why it matters:** 
Adds a high-quality, free image source that doesn't require paid API keys, lowering the barrier for new users to run Pictovap with real (non-mock) candidates.

**Proposed approach:**
- Implement `src/pictovap/providers/openverse.py` following the existing provider interface.
- Handle pagination and rate limiting.
- Map results to Pictovap's `candidate` model (source path, metadata, license info).
- Add unit tests with mock responses.
- Register the adapter in `src/pictovap/config.py`.

**Acceptance criteria:**
- Adapter connects to the Openverse API and returns candidates.
- Pagination is handled for queries returning many results.
- License information is mapped into the Provenance Pack format.
- Unit tests pass with mocked API responses.

**Credentials required:** Yes (Openverse API key for testing)
**Difficulty:** Medium
