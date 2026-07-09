# 🏛 System Architecture

This document describes the high-level architecture of Pictova. It is designed to help developers understand the core abstractions, the data flow, and the reasoning behind structural decisions.

---

## 1. Core Philosophy

Pictova is not just a script; it is a **pipeline-based engine**. It strictly isolates the extraction of data from the transformation and loading of data.

- **Immutability:** Source images are never mutated. Processed images are completely separate artifacts.
- **Stateless Modules:** The engine modules (`selector`, `processor`, `metadata`, `publisher`) receive state, execute their logic, and return a result without side effects.
- **Predictable Degradation:** The Vision Chain gracefully degrades. If Claude goes down, it falls back to Gemini. If the internet goes down, it uses local LLM extraction.

---

## 2. Pipeline Execution Flow

When a user runs `pictova attach`, the execution follows this lifecycle:

```mermaid
sequenceDiagram
    participant CLI as CLI / App
    participant Engine as Engine (attach.py)
    participant Selector as Selector
    participant Processor as Processor
    participant Vision as Vision Chain
    participant WP as WordPress API
    
    CLI->>Engine: run_attach_pipeline(post_id)
    activate Engine
    
    Engine->>WP: fetch_post_context()
    WP-->>Engine: Post HTML + Metadata
    
    Engine->>Selector: select_media(context)
    activate Selector
    Selector->>Selector: Generate Semantic Query
    Selector->>Selector: Query FTS Index & Unsplash
    Selector-->>Engine: candidate_assets[]
    deactivate Selector
    
    Engine->>Processor: process_batch(candidate_assets)
    activate Processor
    Processor->>Processor: Resize, WebP encode, Cinematic Grade
    Processor-->>Engine: processed_images[]
    deactivate Processor
    
    Engine->>Vision: generate_metadata(processed_images, context)
    activate Vision
    Vision->>Vision: Query Local LLM (LM Studio)
    Vision->>Vision: Fallback to Gemini/Claude
    Vision-->>Engine: metadata_dict{alt, title, caption}
    deactivate Vision
    
    Engine->>WP: upload_images_batch(processed_images, metadata_dict)
    activate WP
    WP-->>Engine: Block HTML string
    deactivate WP
    
    Engine->>Engine: Merge blocks & ensure Integrity Guard
    
    Engine->>CLI: Return execution results
    deactivate Engine
```

---

## 3. Directory Structure

To maintain strict boundary enforcement, the codebase is layered:

```text
src/
├── pictova/
│   ├── app/           # External entrypoints (CLI, HTTP REST APIs, Jobs)
│   ├── engine/        # The brain: pure business logic and the pipeline execution
│   ├── profiles/      # Site-specific configurations (e.g. yoldaolmak.py)
│   └── providers/     # External integrations (WordPress, Unsplash, DepositPhotos)
├── utils/             # Cross-cutting concerns (logging, env parsing)
├── visual_memory/     # Models and logic for the SQLite FTS asset index
└── services/          # Low-level service implementations
```

> [!WARNING]  
> **Strict Layering Rule:** `app/` may import from `engine/`. `engine/` may import from `providers/`. `providers/` and `utils/` cannot import from `engine/`. This prevents circular dependencies and tight coupling.

---

## 4. The Vision Chain

The Vision Chain is the most computationally expensive and complex part of Pictova. It is responsible for generating human-like, SEO-optimized metadata from raw pixels.

```mermaid
flowchart TD
    A[Processed WebP Image] --> B{LM Studio Local?}
    B -->|Yes| C[Qwen2-VL / Local LLaVA]
    B -->|No| D{Google Gemini Available?}
    
    C -->|Failure/Timeout| D
    
    D -->|Yes| E[Gemini 1.5 Flash]
    D -->|Quota Exceeded| F[Anthropic Claude CLI]
    
    E -->|Success| G[JSON Parser]
    F -->|Success| G
    C -->|Success| G
    
    G --> H((Validated Metadata Object))
```

### Why fallback?
APIs have rate limits, and network connectivity can fluctuate. By utilizing a **Chain of Responsibility** pattern, Pictova guarantees that every image receives metadata, eliminating pipeline bottlenecks.

---

## 5. Visual Memory Index

The selection phase relies on an extremely fast, offline Full-Text Search (FTS5) index built on SQLite.

Instead of scanning terabytes of images on demand, Pictova maintains `visual_memory.db`.
- **Apple ML Integration:** Apple Photos automatically tags images with `labels` (e.g., "mountain", "sunset"). Pictova extracts these natively.
- **FTS5:** Enables millisecond querying across `location`, `scene`, `activity`, and `camera_model`.

> [!TIP]
> Refer to `docs/concepts/visual-memory.md` for instructions on how to force a rebuild of the visual memory index.
