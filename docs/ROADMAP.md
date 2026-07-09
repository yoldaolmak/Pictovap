# 🗺 Pictova Development Roadmap

Pictova aims to become the industry standard for content-driven visual automation. Our development roadmap is structured to evolve the project from a local CLI tool into a robust, enterprise-grade Python SDK and eventually a premium SaaS engine.

---

## 🎯 Phase 1: Core Intelligence & Native Engine (Current)
**Goal:** Perfect the core visual search, image processing pipeline, and the AI-powered Metadata Vision Chain.

- [x] **Native Engine Transition:** Deprecate legacy procedural code in favor of a clean, modular class-based pipeline (`selector`, `processor`, `metadata`, `publisher`).
- [x] **Heading-Aware Selection:** Implement semantic matching of images based on `H2/H3` post structure, and apply SEO-optimized titles and slugs.
- [x] **Vision Chain:** Establish a highly resilient local LLM -> Gemini -> Claude API fallback chain for WCAG-compliant image tagging.
- [ ] **Multi-Source Fallback:** Implement automated fallback to the Unsplash API if local Visual Memory index queries do not yield enough diverse candidates.

---

## 🚀 Phase 2: Premium Features & Stock Integrations (Next Up)
**Goal:** Integrate commercial stock libraries, advanced asset quality scoring, and programmatic image optimization.

- [ ] **Pictova Depot (DepositPhotos API):** Add support for DepositPhotos integration to automatically search, purchase, and download licensed stock photos when local or free options are insufficient.
- [ ] **Advanced Quality Gate:** Implement ML-based quality controls to filter out blurry, low-resolution, or low-aesthetic-score images.
- [ ] **WebP Optimization V2:** Support lossy vs. lossless WebP configuration, strip/preserve specific EXIF metadata profiles, and add custom image watermark overlays.

---

## 📦 Phase 3: SDK & Multi-Platform Support (Developer Focus)
**Goal:** Expand Pictova's footprint beyond WordPress and simplify developer integration.

- [ ] **PyPI Release:** Package and publish `pictova` to PyPI (`pip install pictova`).
- [ ] **Ghost CMS & Strapi Publishers:** Implement publisher adapters for Headless CMS architectures (Ghost, Strapi, Contentful).
- [ ] **Custom Vision Templates:** Allow developers to define custom metadata prompt templates (e.g. strict technical analysis vs. poetic captions).

---

## 🌐 Phase 4: Platform & UI Dashboard (Long Term)
**Goal:** Turn Pictova into an easily manageable web service with a clean interface.

- [ ] **Web Administration Dashboard:** A Next.js/Vite frontend for monitoring visual memory health, previewing candidate selections, and manually correcting AI captions.
- [ ] **Asynchronous Task Queue:** SQLite/Redis-backed background worker queue to handle heavy Vision Chain processing asynchronously.
