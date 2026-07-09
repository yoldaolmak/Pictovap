# PICTOVA - CURRENT PROJECT MEMORY

**Date:** June 2026
**Purpose:** Quick context resume for AI agents starting a new session. Read this file to understand the current state without reading long transcripts.

## Core Project Overview
- **Pictova** is a robust photo/video indexing and AI metadata generation system for macOS Photos Library (`osxphotos`).
- It extracts local metadata and uses AI models (Gemini Flash / Claude / Codex via `vision_chain.py`) to generate SEO-friendly, rich textual metadata (title, alt text, description, summary, caption) for WordPress blog publishing.

## Latest Accomplishments & Architecture Updates (Recent Context)
1. **Apple ML Labels Integration:**
   - The database (`asset_index` in `data/visual_memory.db`) now includes an `apple_labels_json` column.
   - The indexer scripts (`scripts/index_turkey_photos.py` and `scripts/index_country_photos.py`) have been updated to extract native Apple ML tags (`photo.labels`) and insert them into the database during the initial library scan.
2. **Context-Aware Vision Prompts:**
   - `scripts/fast_scan.py` now retrieves these `apple_labels_json` values and passes them to the AI vision chain.
   - The AI models now use `apple_ml_labels` as additional context for higher accuracy.
3. **Refined Caption Tone (Kemal Kaya Style):**
   - The `caption` prompt generation in `src/pictova/engine/vision_chain.py` was heavily customized. 
   - **Crucial Rule:** The AI must NEVER write dry, clinical descriptions like "Bu fotoğrafta deniz ve ağaç var". 
   - **Crucial Rule:** Captions must blend factual/geographic knowledge of the location with the scene's atmosphere using an active, first-person narrative (e.g., "Gümüşlük, göz ardı edilse de Bodrum'un en sakin tatil köşesi hala.", "Suya kurulan masalarda, batan güneşe bakarak günü uğurladığımız yerdir burası.").

## Active Processes
- `fast_scan.py` is regularly run (sometimes by the user from their native terminal due to TCC macOS full-disk access restrictions on the `Photos.sqlite` database).
- When the user runs the scan from their terminal, it successfully processes images, using multiple keys in the `.env` file to handle API rate limits.

## Next Steps / How to Continue
- If the user asks to "check status", query the `visual_memory.db` for `vision_scan_status` ('done', 'pending', 'error').
- Keep token usage optimized.
- Do NOT output large code diffs to the screen unless explicitly requested. Just do the work and provide a brief status update.
