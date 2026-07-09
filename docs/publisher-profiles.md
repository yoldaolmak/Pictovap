# Publisher Profiles

Pictovap is designed to support multiple publishers from a single engine. A **Publisher Profile** allows you to define brand-specific rules for how images are selected, processed, and placed.

## Configuration Model

The `PublisherProfile` (found in `src/pictova/core/profile.py`) is a configuration model that encapsulates:

- **Brand Name**: Used in AI prompt generation and logging.
- **CMS Type**: e.g., `wordpress`, `ghost`, `strapi`. Determines which adapter will be used in the CMS Placement phase.
- **Language**: The primary language for generated alt text and captions (e.g., `en`, `tr`).
- **Image Sources**: Which providers should be queried (e.g., `local`, `unsplash`, `depositphotos`).
- **Output Rules**: Parameters for resizing, WebP conversion, and color grading.
- **Filename Rules**: How generated files should be named (e.g., lowercase, kebab-case, appended hash).
- **Alt Text & Caption Rules**: Specific prompt instructions (e.g., "Do not use the word 'image'").
- **Editorial Preferences**: General style guidelines for the brand.
- **Forbidden Patterns**: A list of clichés or concepts to explicitly avoid (e.g., "tourists holding maps").

## Usage

When running Pictovap, you pass the profile name to the CLI or API (e.g., `--site myblog`). The engine loads the corresponding `PublisherProfile` and injects it into the `VisualBrief` and `FitScore` generation phases to ensure the final output matches the brand's identity.
