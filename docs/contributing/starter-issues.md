# Starter Issues Backlog

This document maintains a backlog of verified, scope-controlled issues suitable for first-time contributors.

These are now open on the [GitHub issue board](https://github.com/yoldaolmak/Pictovap/issues). To claim one, comment on the issue with your intended approach.

## 1. Add Pixabay image source adapter
**Problem:** We need another free, CC0 public image source alongside Openverse.
**Expected files:** `src/pictova/providers/pixabay.py`, tests.
**Acceptance Criteria:** Adapter connects to Pixabay API, handles pagination, and respects Pictovap's `candidate` model.
**Difficulty:** Medium
**Credentials required:** Yes (Pixabay API key for testing)

## 2. Add Wikimedia Commons image source adapter
**Problem:** Editorial/factual content needs a freely licensed media source beyond stock photo APIs.
**Expected files:** `src/pictova/providers/wikimedia.py`, tests.
**Acceptance Criteria:** Adapter searches Commons and respects Pictovap's `candidate` model.
**Difficulty:** Medium
**Credentials required:** No

## 3. Add Markdown frontmatter support
**Problem:** The `VisualBrief` relies heavily on headings. It should also read standard YAML frontmatter for metadata (e.g., categories, target audience).
**Expected files:** `src/pictova/core/primitives.py` (where `VisualBrief` is built)
**Acceptance Criteria:** Frontmatter variables pass into the Vision context block.
**Difficulty:** Low
**Credentials required:** No

## 4. Add local folder image metadata loader
**Problem:** The local mock provider only reads file names. It should read EXIF data to populate candidate metadata.
**Expected files:** `src/pictova/providers/local.py`
**Acceptance Criteria:** Uses Pillow to extract EXIF tags and maps them to candidate dict.
**Difficulty:** Low
**Credentials required:** No

## 5. Improve duplication risk scoring
**Problem:** Images with similar visual characteristics shouldn't be placed next to each other.
**Expected files:** `src/pictova/engine/quality.py`
**Acceptance Criteria:** Basic structural similarity check is added to the fit score math.
**Difficulty:** High
**Credentials required:** No

## 6. Add license confidence mapping
**Problem:** Different APIs return licenses in different string formats. We need a unified enum.
**Expected files:** `src/pictova/core/primitives.py`
**Acceptance Criteria:** `LicenseType` enum replaces raw string passing for Provenance Packs.
**Difficulty:** Low
**Credentials required:** No

## 7. Add additional sample publisher profile
**Problem:** Our examples only cover travel blogs. We need an e-commerce profile.
**Expected files:** `examples/profiles/ecommerce.yaml`
**Acceptance Criteria:** YAML profile focused on product-centric imagery.
**Difficulty:** Very Low
**Credentials required:** No

## 8. Add additional sample article type
**Problem:** Showcasing versatility requires more input examples.
**Expected files:** `examples/articles/tech-review.md`
**Acceptance Criteria:** A valid markdown article demonstrating a tech review layout.
**Difficulty:** Very Low
**Credentials required:** No

## 9. Improve alt text templates
**Problem:** The default external model prompts sometimes generate overly verbose alt text.
**Expected files:** `src/pictova/vision_templates.py`
**Acceptance Criteria:** Add a strict length constraint to the system prompt and verify output.
**Difficulty:** Low
**Credentials required:** Yes (API key for manual testing)

## 10. Add docs link checker expansion
**Problem:** The Makefile `check-docs` only tests `docs/README.md`. It needs to crawl all markdown files.
**Expected files:** `tests/unit/test_demo.py` (or new test file)
**Acceptance Criteria:** Test recursively finds all `.md` files and validates relative links.
**Difficulty:** Medium
**Credentials required:** No

## 11. Add OpenSSF Scorecard preparation
**Problem:** To ensure OSS hygiene, we should run the OpenSSF Scorecard tool via GitHub Actions.
**Expected files:** `.github/workflows/scorecard.yml`
**Acceptance Criteria:** Workflow is configured strictly following OpenSSF guidelines in dry-run mode.
**Difficulty:** Medium
**Credentials required:** No
