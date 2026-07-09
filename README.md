<div align="center">
  <br />
  <img src="https://raw.githubusercontent.com/yoldaolmak/Pictovap/main/docs/assets/pictova-banner.png" alt="Pictova" width="800" onerror="this.style.display='none'"/>
  <h1 align="center">Pictova</h1>
  <p align="center">
    <strong>The Visual Intelligence & Automation Layer for Content Publishers</strong>
  </p>
  <p align="center">
    Automate the entire image lifecycle — from semantic selection and cinematic grading to AI metadata generation and direct CMS integration.
  </p>

  <p align="center">
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License: MIT" /></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+" /></a>
    <a href="https://github.com/yoldaolmak/Pictovap/actions"><img src="https://img.shields.io/badge/tests-51%20passed-brightgreen.svg?style=for-the-badge&logo=github" alt="Tests" /></a>
    <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge" alt="PRs Welcome" /></a>
  </p>
</div>

<hr />

## 💡 Why Pictova?

Visual asset management is the most tedious, repetitive bottleneck in digital publishing. Content creators lose hours every week on mundane visual operations. Pictova reclaims that time.

| The Problem | Manual Era | With Pictova 🚀 |
| :--- | :--- | :--- |
| **Contextual Discovery** | 20 mins searching folders per article | **Automatic** via semantic matching to `H2/H3` headings |
| **SEO & Accessibility** | 5 mins typing `alt` & `title` tags per image | **Automatic** via Vision Chain (LLMs contextually analyze visuals) |
| **Optimization & Branding** | 10 mins resizing, color grading, WebP | **Automatic** adaptive processor with cinematic YO filters |
| **CMS Publishing** | 10 mins dragging, dropping, aligning | **Automatic** Gutenberg block injection via REST API |

> [!TIP]
> What used to take **45–60 minutes** per article now executes in **under 60 seconds** via a single terminal command.

---

## 🏗 System Architecture

Pictova operates as a high-performance modular pipeline.

```mermaid
graph LR
    classDef primary fill:#2563eb,stroke:#1d4ed8,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef secondary fill:#475569,stroke:#334155,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef storage fill:#059669,stroke:#047857,stroke-width:2px,color:#fff,rx:8px,ry:8px;

    WP((WordPress Post)):::secondary --> |1. Analyze Context| Selector:::primary
    
    subgraph Sources
        VM[(Visual Memory SQLite)]:::storage
        UN[Unsplash API]:::storage
    end
    
    Selector --> |2. Query| Sources
    Sources --> |3. Candidates| Processor:::primary
    
    Processor --> |4. WebP / Grade| Metadata:::primary
    
    subgraph Vision Chain
        LLM[Local LLM]:::secondary
        GEM[Gemini Flash]:::secondary
        CLD[Claude CLI]:::secondary
        LLM --> GEM --> CLD
    end
    
    Metadata --> |5. Analyze| Vision Chain
    Vision Chain --> |6. Alt/Title/Desc| Publisher:::primary
    Publisher --> |7. Gutenberg Insert| WP
```

For an in-depth dive into our architecture, see the [Architecture Documentation](docs/ARCHITECTURE.md).

---

## 🌟 Premium Features

- 🧠 **Heading-Aware Selection**  
  Pictova doesn't just dump images at the end of a post. It parses the `H2` and `H3` semantic structure of your article and mathematically aligns the most contextually relevant image to each specific section.
  
- 🎨 **Cascading Vision Chain**  
  Generates rich metadata utilizing a resilient fallback chain:
  1. **Local LLM** (LM Studio / Qwen2-VL) — 100% private, free, offline execution.
  2. **Gemini Flash** — Google AI Studio (Free tier fallback).
  3. **Claude CLI** — Enterprise-grade safety net.

- 🏷️ **Field-Specific Intent**  
  WordPress fields are populated with distinct, targeted objectives:
  - `alt`: Strict visual descriptions for screen readers (WCAG compliant).
  - `title`: Keyword-rich naming for Search Engine Indexing.
  - `caption`: Engaging, contextual storytelling for human readers.

- 🖼️ **Cinematic Color Grading**  
  Built-in adaptive filters automatically normalize brightness, contrast, and saturation, applying a signature look (warm highlights, cool shadows) without touching Adobe Lightroom.

---

## 🚀 Quickstart

Get Pictova running in under two minutes.

### 1. Installation

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install core and dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Configuration

Copy the template and configure your API tokens.

```bash
cp .env.example .env
```
> [!IMPORTANT]
> You must provide `WP_URL`, `WP_USER`, and `WP_APP_PASSWORD` in your `.env` file to communicate with your WordPress installation.

### 3. Verify Health

Ensure the engine is correctly initialized:

```bash
pictova health
```

### 4. Execute Pipeline

Analyze a post, select 4 context-aware images, grade them, generate metadata, and publish:

```bash
pictova attach --site myblog --post 1042 --count 4 --engine native
```

### 5. Programmatic SDK Usage

Developers can import and build upon the Pictova engine directly in Python:

```python
from pictova import analyze_image_vision_chain, resolve_source_images
from pictova.services.wordpress import YOWordPressUploader

# 1. Resolve context-aware assets semantically
assets = resolve_source_images(
    source="auto",
    count=2,
    name=None,
    query="Akyaka Plajı ve Deniz",
    location_query="Akyaka",
    content_filter=None,
    post_context={"title": "Akyaka Gezi Rehberi"}
)

# 2. Analyze image using the Vision Chain fallback structure
metadata = analyze_image_vision_chain(
    image_path="docs/assets/pictova-banner.png",
    location_hint="Akyaka",
    post_context={"title": "Akyaka Gezi Rehberi"}
)
print(f"Alt tag: {metadata['alt']}")

# 3. Direct WordPress publishing using YOWordPressUploader
uploader = YOWordPressUploader(site="yoldaolmak")
result = uploader.upload_media(
    file_path="docs/assets/pictova-banner.png",
    title=metadata["title"],
    alt_text=metadata["alt"],
    description=metadata["description"],
    caption=metadata["caption"],
)
```

---

## 📚 Documentation Portal

We maintain comprehensive documentation for all user roles.

- **[Developer Guide](docs/DEVELOPER.md)**: Setup, standards, and CLI tooling.
- **[Architecture & Design](docs/ARCHITECTURE.md)**: Deep dive into the pipeline and data flows.
- **[CLI Reference](docs/CLI_REFERENCE.md)**: Exhaustive manual for `attach`, `plan`, `process`, and `serve`.
- **[Roadmap](docs/ROADMAP.md)**: Future milestones and strategic goals.

---

## 🤝 Contributing

We are thrilled to welcome contributors to Pictova. Whether it's adding Headless CMS adapters (Ghost, Strapi), integrating new stock photo providers, or optimizing our Local LLM memory footprint, your PRs are highly appreciated.

Please review our [Contributing Guidelines](CONTRIBUTING.md) before opening a Pull Request.

---

<div align="center">
  <p>Built with ❤️ for content creators by <a href="https://yoldaolmak.com">Meridyen / Yoldaolmak</a></p>
  <p>Licensed under the <strong>MIT License</strong>.</p>
</div>
