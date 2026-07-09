# Pictova 🚀

**The Visual Intelligence & Automation Layer for Content Publishers**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-51%20passed-brightgreen.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Pictova is an open-source, AI-powered visual asset automation engine built for digital publishers. It automates the entire image lifecycle — from semantic image selection and adaptive color grading to AI-generated multilingual metadata and direct Gutenberg block insertion — so content creators can focus on writing.

```bash
# One command: analyze post, select images, process, generate metadata, publish
pictova attach --site myblog --post 1042 --count 4 --engine native
```

---

## 💡 Why Pictova Matters

Visual asset management is one of the biggest time sinks in digital publishing:

| Problem | Manual Effort | With Pictova |
|---------|--------------|--------------|
| Finding relevant images per section | 15–30 min/article | **Automatic** — semantic matching to H2/H3 headings |
| Writing SEO alt/title/caption tags | 2–5 min/image | **Automatic** — AI vision chain with distinct field roles |
| Resizing, compressing, WebP encoding | 5–10 min/batch | **Automatic** — adaptive processor with cinematic grading |
| Inserting images at correct positions | 5–10 min/article | **Automatic** — Gutenberg block injection at heading points |

**Result:** What used to take 45–60 minutes per article now takes seconds.

---

## 📈 Production Use

Pictova is not a proof-of-concept — it runs **daily in production** powering [yoldaolmak.com](https://yoldaolmak.com), a travel content platform with 40,000+ indexed photos.

- **10+ hours saved weekly** on visual operations
- **25% improvement** in image search impressions through contextual SEO metadata
- **Zero-touch publishing:** Authors write text; Pictova handles every visual aspect automatically

---

## 🏗 Architecture

Pictova operates as a modular pipeline with four distinct stages:

```
┌──────────────────────────────────────────────────────────┐
│                    Pictova Pipeline                        │
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  1. Selector  │───▶│ 2. Processor │───▶│ 3. Metadata  │ │
│  │              │    │              │    │              │ │
│  │ Semantic     │    │ Resize/Crop  │    │ Vision Chain │ │
│  │ search across│    │ WebP encode  │    │ (Local LLM   │ │
│  │ Visual Memory│    │ Color grade  │    │  → Gemini    │ │
│  │ + Unsplash   │    │ EXIF strip   │    │  → Claude)   │ │
│  └──────────────┘    └──────────────┘    └──────┬───────┘ │
│                                                  │         │
│                                          ┌───────▼───────┐ │
│                                          │ 4. Publisher   │ │
│                                          │               │ │
│                                          │ WP REST API   │ │
│                                          │ Gutenberg     │ │
│                                          │ block insert  │ │
│                                          └───────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Core Components

| Module | Role | Tech |
|--------|------|------|
| **Selector** | Semantic image search matched to post headings | SQLite FTS5, Apple Photos index, Unsplash API |
| **Processor** | Adaptive image optimization & cinematic grading | PIL/Pillow, NumPy, custom YO filter pipeline |
| **Metadata (Vision Chain)** | AI-generated alt/title/caption/description | Local LLM (LM Studio) → Gemini Flash → Claude CLI fallback |
| **Publisher** | Gutenberg block insertion via WordPress REST API | WordPress REST API, heading-aware block placement |

For detailed architecture docs, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🌟 Key Features

- 🧠 **Heading-Aware Selection** — Images aren't randomly placed. Pictova reads the H2/H3 structure of your article and assigns each image to the most relevant section.

- 🎨 **Vision Chain with Fallback** — Generates rich metadata using a cascading chain of AI models:
  1. **Local LLM** (LM Studio / Qwen2-VL) — free, private, fast
  2. **Gemini Flash** — free tier, high quality
  3. **Claude CLI** — premium fallback

- 🏷️ **Distinct Metadata Roles** — Each WordPress field serves a different audience:
  - `alt` → Screen readers & accessibility (plain visual description)
  - `title` → Search engines & SEO (keyword-rich heading)
  - `caption` → Human readers (contextual, engaging note)
  - `description` → Rich detail combining location + visual elements

- 🔗 **SEO-Friendly Renaming** — Files are dynamically renamed based on location and content context (e.g., `bodrum-gumusluk-sunset-harbor.webp`)

- 🖼️ **Adaptive Color Grading** — Built-in cinematic color filters automatically normalize brightness, saturation, contrast, and apply signature warm highlights / cool shadows

- 📚 **Visual Memory** — SQLite-based index of 40,000+ personal photos with Apple Photos integration, location data, AI scene tags, and full-text search

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your credentials:
#   GEMINI_API_KEY            — Google AI Studio (free tier)
#   WP_USER, WP_APP_PASSWORD  — WordPress application password
#   UNSPLASH_ACCESS_KEY       — Unsplash API (optional)
```

### 3. Verify

```bash
pictova health
# Output: {"status": "ok", "service": "pictova", "vision_chain": {...}}
```

### 4. Run

```bash
# Select 4 images, generate metadata, and publish to a WordPress post
pictova attach --site myblog --post 1234 --count 4 --engine native
```

---

## 🗺 Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **Core Engine** | ✅ Complete | Native pipeline, heading-aware selection, vision chain |
| **Local LLM Support** | ✅ Complete | LM Studio / Qwen2-VL integration for offline analysis |
| **Visual Memory** | ✅ Complete | 40K+ photo SQLite index with Apple Photos sync |
| **Stock API Fallback** | 🔄 In Progress | Unsplash automatic fallback when local archive has no match |
| **Headless CMS Adapters** | 📋 Planned | Ghost, Strapi, Shopify adapters |
| **Task Queue** | 📋 Planned | Celery/Redis async batch processing |
| **Web Dashboard** | 📋 Planned | Browser-based UI for non-CLI users |

Full roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## 🤝 Contributing

We welcome contributions of all kinds! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development environment setup
- Code architecture rules
- Testing with `pytest` (51 unit + integration tests)
- Branch naming and commit message conventions

**Good first issues** are labeled in the [Issues](https://github.com/yoldaolmak/Pictovap/issues) tab.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, pipeline stages, data flow |
| [Developer Guide](docs/DEVELOPER.md) | Dev environment setup, code standards |
| [CLI Reference](docs/CLI_REFERENCE.md) | Full command reference (`attach`, `plan`, `process`, `serve`) |
| [Roadmap](docs/ROADMAP.md) | Product development vision and milestones |

---

## 📄 License

[MIT License](LICENSE) — Free to use, fork, and build upon.
