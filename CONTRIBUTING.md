# Contributing to Pictova

Thank you for your interest in contributing to Pictova! Whether you're fixing a bug, improving documentation, or proposing a new feature, your contribution is welcome.

## 🚀 Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
```

### 2. Set Up Development Environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
```

### 3. Run the Test Suite

```bash
python3 -m pytest -q                  # all tests
python3 -m pytest tests/unit/         # unit only
python3 -m pytest tests/integration/  # integration only
```

Integration tests require no WordPress credentials — they test the CLI contract with structured failure responses.

---

## 📝 How to Contribute

### Bug Reports
Open an [issue](https://github.com/yoldaolmak/Pictovap/issues) with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

### Feature Proposals
Open a [discussion](https://github.com/yoldaolmak/Pictovap/issues) describing:
- The problem you're solving
- Your proposed solution
- Any alternatives considered

### Pull Requests
1. Branch from `main`
2. Write or update tests — all must pass
3. Update relevant docs in `docs/`
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Submit a PR with a clear description

---

## 🏛 Architecture Rules

Pictova's codebase follows strict layering:

| Layer | Location | Rule |
|-------|----------|------|
| **App** | `src/pictova/app/` | HTTP/CLI entry points only — no business logic |
| **Engine** | `src/pictova/engine/` | Core logic — no direct I/O, use injected providers |
| **Providers** | `src/pictova/providers/` | External integrations (WordPress, Unsplash, etc.) |
| **Legacy** | `src/core/`, `src/main.py` | Do not add new code here — migrate into `src/pictova/engine/` |

**Do not delete legacy modules** if anything still imports them — deprecate gradually.

---

## 🔤 Naming Convention

- Product name: **Pictova**
- CLI command: `pictova`
- Python package root: `src.pictova`

See [Brand & Naming Doctrine](docs/architecture/naming.md) for details.

---

## 📋 Commit Messages

Follow the conventional commits format:

```
type: short description
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `ops`

Examples:
- `feat: add DepositPhotos provider`
- `fix: handle HEIC files in vision chain`
- `docs: update CLI reference for plan command`

---

## 🧪 Testing

Every new feature or bug fix must include tests:

```bash
# Run the full suite before submitting
python3 -m pytest -q
```

Current test coverage: **51 tests** across unit and integration suites.

---

## 📖 Documentation

- All docs are in English
- Every new feature needs at least one updated doc page
- Documentation structure:
  - **Concepts** = What and Why
  - **Guides** = How-to
  - **Reference** = Complete specification
  - **Architecture** = Design decisions

---

## 🙏 Code of Conduct

Be respectful, constructive, and inclusive. We're building something useful together.
