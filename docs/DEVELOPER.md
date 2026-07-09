# 💻 Developer Guide

Welcome to the Pictova developer guide. This document outlines everything you need to set up your local development environment, understand our tooling, and contribute high-quality code.

---

## 🛠 Local Environment Setup

Pictova is built with Python 3.9+ and relies heavily on a clean, isolated virtual environment.

### 1. Bootstrap the Project

```bash
# Clone the repository
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap

# Initialize a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (including dev tools)
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Environment Variables

The application relies on `.env` for secrets and configuration.

```bash
cp .env.example .env
```

Open `.env` and configure at minimum:
- `WP_URL`, `WP_USER`, `WP_APP_PASSWORD` (For integration testing against WordPress).
- `GEMINI_API_KEY` (Required for Vision Chain tests).

---

## 🧪 Testing Strategy

We maintain a rigorous test suite using `pytest`. Currently, the project has **51 passing tests** across unit and integration boundaries.

> [!IMPORTANT]  
> All PRs must pass the test suite before they can be merged. Do not skip tests.

### Running Tests

```bash
# Run the entire suite
python3 -m pytest -q

# Run only unit tests (fast, no external API calls)
python3 -m pytest tests/unit/

# Run integration tests (requires .env configuration)
python3 -m pytest tests/integration/
```

### Writing Tests

- Place new unit tests in `tests/unit/`.
- Ensure you mock external dependencies (like `requests` or `osxphotos`) using `unittest.mock`.
- Integration tests must gracefully skip if the required `.env` variables are missing, ensuring they don't break CI/CD pipelines.

---

## 🏗 Coding Standards & Conventions

We enforce strict coding standards to keep the repository maintainable.

### Python Style
- **Type Hints:** All function signatures must include Python type hints.
  ```python
  # ❌ Bad
  def process_image(filepath, target_width):
      pass

  # ✅ Good
  def process_image(filepath: str, target_width: int) -> dict:
      pass
  ```
- **Docstrings:** Use Google-style docstrings for public classes and complex functions.
- **Line Length:** Try to keep lines under 120 characters.

### Architecture Rules
As detailed in the [Architecture Guide](ARCHITECTURE.md):
- **App Layer (`src/pictova/app`)**: Contains HTTP servers, CLI entrypoints, and argument parsers. *No business logic allowed.*
- **Engine Layer (`src/pictova/engine`)**: Contains the core logic. *Cannot import from app/.*
- **Providers Layer (`src/pictova/providers`)**: External API integrations (WordPress, Unsplash). *Cannot import from engine/.*

---

## 🚀 Building & Shipping

If you are developing the CLI, you can test it directly via the setuptools console script:

```bash
# Ensure you are in your active virtual environment
pictova --help
```

### Submitting a Pull Request
1. Branch from `main` (`git checkout -b feature/your-feature-name`).
2. Write your code and tests.
3. Ensure `python3 -m pytest` passes completely.
4. Commit using Conventional Commits format (`feat: ...`, `fix: ...`, `docs: ...`).
5. Open a Pull Request and describe the problem you are solving.

> [!TIP]
> If you are adding a new Provider (e.g., a new Stock Photo API), please update `docs/guides/adding-sources.md` alongside your PR.
