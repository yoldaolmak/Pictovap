# Developer Guide

This guide covers the local environment, tests, and contribution workflow for
Pictovap.

---

## Local Environment Setup

Pictovap supports Python 3.10+ and should be developed in an isolated virtual
environment.

Check the interpreter before creating the environment. On systems where
`python3` points to an older system Python, use an installed 3.10+ binary such
as `python3.11`.

### 1. Bootstrap the Project

```bash
# Clone the repository
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap

# Initialize a clean virtual environment
python3 --version
python3 -m venv .venv
source .venv/bin/activate

# Install the package and all local contributor checks in editable mode
make install
```

### 2. Configure Environment Variables (Optional)

The credential-free demo and unit suite do not require a `.env` file. Copy it
only when exercising a credentialed image source, CMS adapter, or live vision
provider.

```bash
cp .env.example .env
```

Open `.env` and configure only the integration you are exercising:
- `WP_URL`, `WP_USER`, `WP_APP_PASSWORD` (for local WordPress integration work).
- `GEMINI_API_KEY` (optional; enables live Gemini vision analysis).

---

## Testing Strategy

The unit suite is deterministic and does not call external APIs. Integration
tests must skip cleanly when their required credentials are unavailable.

For the complete local gate, run `make contribution-check`. It includes the
unit suite, lint/type checks, documentation links, and security hygiene without
requiring Node/npm.

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

## Coding Standards & Conventions

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
- **App Layer (`src/pictovap/app`)**: Contains HTTP servers, CLI entrypoints, and argument parsers. *No business logic allowed.*
- **Engine Layer (`src/pictovap/engine`)**: Contains the core logic. *Cannot import from app/.*
- **Providers Layer (`src/pictovap/providers`)**: External image-source integrations
  such as Unsplash, DepositPhotos, and Openverse. *Cannot import from engine/.*
- **Publishers and Services Layers (`src/pictovap/publishers`,
  `src/pictovap/services`)**: CMS integrations such as Ghost, Strapi, and
  WordPress.

---

## Building & Shipping

If you are developing the CLI, you can test it directly via the setuptools console script:

```bash
# Ensure you are in your active virtual environment
pictovap --help
pictovap --version
```

### Submitting a Pull Request
1. Branch from `main` (`git checkout -b feature/your-feature-name`).
2. Write your code and tests.
3. Ensure `python3 -m pytest` passes completely.
4. Commit using Conventional Commits format (`feat: ...`, `fix: ...`, `docs: ...`).
5. Open a Pull Request and describe the problem you are solving.

> [!TIP]
> If you are adding a new image source adapter (e.g., a new stock photo API), please update `docs/adapters/image-sources.md` alongside your PR.
