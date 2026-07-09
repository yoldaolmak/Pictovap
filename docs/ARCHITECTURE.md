# 🏛 Pictova Architecture

Pictova is built as a **pipeline-oriented visual intelligence engine**. Its architecture focuses on extreme modularity, allowing images to flow from discovery to WordPress insertion through distinct, decoupled layers.

## Core Modules

Pictova's engine is split into highly specialized sub-systems:

### 1. `selector` (Source Resolution)
The entry point of the pipeline. Understands the WordPress post context (slug, headings, excerpt) and resolves the best source images.
- **Visual Memory:** Scans the local SQLite-indexed library (e.g., Apple Photos exports).
- **External APIs:** Unsplash (active), DepositPhotos (planned).
- *Tech:* Semantic matching, location derivation.

### 2. `processor` (Optimization)
Transforms raw image files into web-ready assets.
- Resizes, crops, and compresses to high-quality `.webp`.
- Standardizes color profiles and ensures SEO-friendly resolutions.

### 3. `metadata` (Vision Chain)
The AI brain of Pictova. It generates SEO-optimized `alt`, `title`, and `description` tags by actually "looking" at the image.
- **Vision Chain Fallback:** Evaluates via Gemini Flash -> Codex CLI -> Claude CLI.
- **Heading-Aware:** Considers the specific WordPress H2/H3 heading the image is destined for, generating highly contextual text.

### 4. `attach` (The Orchestrator)
The native engine controller (`execute_native_attach`). It glues the pipeline together:
1. Derives location and headings.
2. Calls `selector`.
3. Distributes headings evenly across selected images.
4. Calls `metadata` and `processor`.
5. Renames files dynamically (e.g., `[location]-[heading]-[scene].webp`).
6. Dispatches to `publisher`.

### 5. `publisher` & `wordpress` (Delivery)
Handles the final mile.
- Uploads assets to the WordPress Media Library.
- Injects native Gutenberg blocks (`<!-- wp:image -->`) directly under the targeted H2/H3 headings via REST API.

---

## The "Native Engine" Paradigm

Pictova is transitioning from a legacy `orchestrator` to the **Native Engine**. The Native Engine operates strictly on pure dictionaries (`Dict[str, Any]`), avoiding heavy stateful classes. This ensures every pipeline step is easily testable, serializable, and ready for future async queueing (Redis/Celery).
