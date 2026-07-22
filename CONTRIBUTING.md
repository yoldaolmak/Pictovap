# 🤝 Contributing to Pictovap

First off, thank you for considering contributing to Pictovap! It's people like you that make open-source software such a powerful tool for the community. 

Whether you're fixing a typo, resolving a critical bug, or proposing a massive architectural improvement, your contribution is highly valued.

> [!TIP]
> The [July 2026 Adapter Sprint](docs/contributing/adapter-sprint.md) is the
> current fastest path to a scoped contribution. Adapter and CMS issues require
> a claim before implementation; issues marked `contribution: no-claim` are
> intentionally independent first PRs and can be submitted directly.

> [!TIP]
> Building an image-source or CMS adapter? Start with
> [Your First Adapter Pull Request](docs/contributing/first-adapter-pr.md).
> It tells you whether to use an in-tree adapter or standalone plugin, then
> gives the shortest verified route for each.

---

## 🚀 How Can I Contribute?

### 1. Reporting Bugs
If you find a bug, please open an [issue](https://github.com/yoldaolmak/Pictovap/issues) and include:
- A clear, descriptive title.
- Steps to reproduce the behavior.
- Expected behavior versus actual behavior.
- Your OS and Python version.

### 2. Suggesting Enhancements
Have an idea that would make Pictovap better? Open a [discussion](https://github.com/yoldaolmak/Pictovap/discussions) describing:
- The specific problem you are trying to solve.
- Your proposed solution.
- Any alternative solutions you have considered.

### 3. Submitting Pull Requests
We love Pull Requests. To ensure a smooth review process:
1. **Fork the repository** and create your branch from `main`.
2. **Set up your environment** by following the [Installation Guide](docs/guides/installation.md).
3. **Run the contributor gate** with `make contribution-check` (after `make install`).
4. **Write tests** for any new logic (all existing and new tests must pass).
5. **Update Documentation** if you change CLI arguments, API endpoints, or core architecture.
6. **Update the CHANGELOG.md** under the `[Unreleased]` section.
7. **Submit your PR** with a descriptive summary of your changes.

---

## 🏛 Architecture Rules

Pictovap's core pipeline is adapter-agnostic: `core/` defines the domain
primitives and formal `Protocol` contracts, and every integration with the
outside world (an image provider, a CMS) is an adapter that implements one
of those contracts.

| Directory | Purpose |
| :--- | :--- |
| `src/pictovap/app/` | CLI entry points (`demo`, `plan`, `report`). No business logic. |
| `src/pictovap/core/` | Domain primitives (`VisualBrief`, `FitScore`, `ProvenancePack`, `CMSPlacement`) and the `ImageSourceAdapter` / `CMSAdapter` protocols in `core/adapters.py`. |
| `src/pictovap/engine/` | Pipeline logic that operates only on `core/` primitives — no adapter-specific code. |
| `src/pictovap/providers/` | Image source adapters (Local, Unsplash, DepositPhotos, Openverse, Pexels). Each implements `search_candidates(query, count)` and must construct without credentials. |
| `src/pictovap/publishers/`, `src/pictovap/services/` | CMS adapters (Ghost, Strapi, WordPress). Each implements `place(placement)` returning `{placed, failed, warnings}`. |

Before adding a new adapter, read the
[Adapter Contribution Guide](docs/contributing/adapters.md) — it covers the
exact interface contract, credential-handling rules, and test expectations.

To start an independent adapter package with the correct entry point and a
passing contract test:

```bash
pictovap scaffold provider <name>
pictovap scaffold cms <name>
```

See [Building Third-Party Adapter Plugins](docs/contributing/plugins.md).

> [!WARNING]
> A new adapter that doesn't conform to `ImageSourceAdapter` or `CMSAdapter`
> (see `src/pictovap/core/adapters.py`) will not be merged. If you're unsure
> where a piece of logic belongs, ask in your PR.

---

## 🔤 Brand & Naming Convention

When writing documentation or code comments, please adhere to our naming conventions:
- **Product Name:** Pictovap (Always capitalized).
- **CLI Command:** `pictovap` (always lowercase; `pictova` remains a deprecated alias).
- **Package Root:** `src/pictovap`.

---

## 📋 Commit Messages

We strictly follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This allows us to auto-generate changelogs and version bumps.

Write commit messages, pull request titles and descriptions, issue text, code
comments, and documentation in English. Generated publisher content remains
language-aware and may use the article's language.

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
