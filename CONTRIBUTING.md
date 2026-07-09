# 🤝 Contributing to Pictovap

First off, thank you for considering contributing to Pictovap! It's people like you that make open-source software such a powerful tool for the community. 

Whether you're fixing a typo, resolving a critical bug, or proposing a massive architectural improvement, your contribution is highly valued.

---

## 🚀 How Can I Contribute?

### 1. Reporting Bugs
If you find a bug, please open an [issue](https://github.com/yoldaolmak/Pictovap/issues) and include:
- A clear, descriptive title.
- Steps to reproduce the behavior.
- Expected behavior versus actual behavior.
- Your OS and Python version.

### 2. Suggesting Enhancements
Have an idea that would make Pictovap better? Open a [discussion](https://github.com/yoldaolmak/Pictovap/issues) describing:
- The specific problem you are trying to solve.
- Your proposed solution.
- Any alternative solutions you have considered.

### 3. Submitting Pull Requests
We love Pull Requests. To ensure a smooth review process:
1. **Fork the repository** and create your branch from `main`.
2. **Set up your environment** by following the [Developer Guide](docs/DEVELOPER.md).
3. **Write tests** for any new logic (all existing and new tests must pass via `pytest`).
4. **Update Documentation** if you change CLI arguments, API endpoints, or core architecture.
5. **Update the CHANGELOG.md** under the `[Unreleased]` section.
6. **Submit your PR** with a descriptive summary of your changes.

---

## 🏛 Architecture Rules

Pictovap is a production-grade project, and we strictly enforce layering to prevent "spaghetti code".

| Layer | Directory | Enforcement Rule |
| :--- | :--- | :--- |
| **App** | `src/pictova/app/` | HTTP/CLI entry points only. Absolutely no business logic. |
| **Core** | `src/pictova/core/` | Defines core domain primitives (`VisualBrief`, `FitScore`, `ProvenancePack`, `CMSPlacement`). |
| **Engine** | `src/pictova/engine/` | Core logic and pipeline processing. Cannot import from `app/`. |
| **Providers** | `src/pictova/providers/` | Data sources and APIs. Cannot import from `engine/`. |
| **Publishers** | `src/pictova/publishers/` | Adapters for CMS targets implementing `PublisherProtocol`. |

> [!WARNING]
> Pull Requests that violate these architectural boundaries will not be merged. If you are unsure where a piece of logic belongs, please ask in your PR!

---

## 🔤 Brand & Naming Convention

When writing documentation or code comments, please adhere to our naming conventions:
- **Product Name:** Pictovap (Always capitalized).
- **CLI Command:** `pictova` (Always lowercase, kept for backward compatibility).
- **Package Root:** `src.pictova`.

---

## 📋 Commit Messages

We strictly follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This allows us to auto-generate changelogs and version bumps.

**Format:**
```text
<type>: <short description>
```

**Allowed Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding or correcting tests
- `ops`: Infrastructure, CI/CD, or deployment changes

**Examples:**
- `feat: add local LLM support via LM Studio`
- `fix: resolve crash when parsing malformed HEIC metadata`
- `docs: update quickstart guide in README`

---

## 🙏 Code of Conduct

In the interest of fostering an open and welcoming environment, we pledge to make participation in our project and our community a harassment-free experience for everyone. Be respectful, be constructive, and let's build something awesome together.
