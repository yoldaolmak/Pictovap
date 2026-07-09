# Starter Issues Backlog

This document maintains a backlog of verified, scope-controlled issues suitable for first-time contributors.

These issues are not yet active on our GitHub board but are ready to be opened. If you want to work on one of these, please open an issue referencing this document!

## 1. Add Openverse image source adapter
**Problem:** We need a free, CC-licensed public image source beyond Unsplash.
**Expected files:** `src/pictova/providers/openverse.py`, tests.
**Acceptance Criteria:** Adapter connects to Openverse API, handles pagination, and respects Pictovap's `candidate` model.
**Difficulty:** Medium
**Credentials required:** Yes (Openverse API key for testing)

## 2. Add Ghost CMS placement adapter
**Problem:** We currently only support WordPress as a reference CMS.
**Expected files:** `src/pictova/publishers/ghost.py`, tests.
**Acceptance Criteria:** Translates `CMSPlacement` primitive into Ghost Admin API payload.
**Difficulty:** Medium
**Credentials required:** Yes (Local Ghost instance)

## 3. Add Strapi CMS placement adapter
**Problem:** Headless CMS support is requested.
**Expected files:** `src/pictova/publishers/strapi.py`, tests.
**Acceptance Criteria:** Translates `CMSPlacement` primitive into Strapi REST API format.
**Difficulty:** Medium
**Credentials required:** Yes (Local Strapi instance)

## 4. Add Markdown frontmatter support
**Problem:** The `VisualBrief` relies heavily on headings. It should also read standard YAML frontmatter for metadata (e.g., categories, target audience).
**Expected files:** `src/pictova/core/metadata_generator.py`
**Acceptance Criteria:** Frontmatter variables pass into the Vision context block.
**Difficulty:** Low
**Credentials required:** No

## 5. Add local folder image metadata loader
**Problem:** The local mock provider only reads file names. It should read EXIF data to populate candidate metadata.
**Expected files:** `src/pictova/providers/local.py`
**Acceptance Criteria:** Uses Pillow to extract EXIF tags and maps them to candidate dict.
**Difficulty:** Low
**Credentials required:** No

## 6. Improve duplication risk scoring
**Problem:** Images with similar visual characteristics shouldn't be placed next to each other.
**Expected files:** `src/pictova/engine/quality.py`
**Acceptance Criteria:** Basic structural similarity check is added to the fit score math.
**Difficulty:** High
**Credentials required:** No

## 7. Add license confidence mapping
**Problem:** Different APIs return licenses in different string formats. We need a unified enum.
**Expected files:** `src/pictova/core/primitives.py`
**Acceptance Criteria:** `LicenseType` enum replaces raw string passing for Provenance Packs.
**Difficulty:** Low
**Credentials required:** No

## 8. Add additional sample publisher profile
**Problem:** Our examples only cover travel blogs. We need an e-commerce profile.
**Expected files:** `examples/profiles/ecommerce.yaml`
**Acceptance Criteria:** YAML profile focused on product-centric imagery.
**Difficulty:** Very Low
**Credentials required:** No

## 9. Add additional sample article type
**Problem:** Showcasing versatility requires more input examples.
**Expected files:** `examples/articles/tech-review.md`
**Acceptance Criteria:** A valid markdown article demonstrating a tech review layout.
**Difficulty:** Very Low
**Credentials required:** No

## 10. Improve alt text templates
**Problem:** The default Claude/Gemini prompts sometimes generate overly verbose alt text.
**Expected files:** `src/pictova/vision_templates.py`
**Acceptance Criteria:** Add a strict length constraint to the system prompt and verify output.
**Difficulty:** Low
**Credentials required:** Yes (API key for manual testing)

## 11. Add docs link checker expansion
**Problem:** The Makefile `check-docs` only tests `docs/README.md`. It needs to crawl all markdown files.
**Expected files:** `tests/unit/test_demo.py` (or new test file)
**Acceptance Criteria:** Test recursively finds all `.md` files and validates relative links.
**Difficulty:** Medium
**Credentials required:** No

## 12. Add OpenSSF Scorecard preparation
**Problem:** To ensure OSS hygiene, we should run the OpenSSF Scorecard tool via GitHub Actions.
**Expected files:** `.github/workflows/scorecard.yml`
**Acceptance Criteria:** Workflow is configured strictly following OpenSSF guidelines in dry-run mode.
**Difficulty:** Medium
**Credentials required:** No
