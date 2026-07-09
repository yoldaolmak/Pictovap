# 💻 CLI Reference

Pictova exposes a simple but powerful command-line interface.

## Global Flags
All commands require the following flags to define the context:
- `--site`: The profile to use (e.g., `yoldaolmak`).
- `--post`: The ID of the WordPress post (e.g., `265713`).

---

## 1. `attach`
The main orchestrator. It performs the complete visual automation lifecycle: discovery, processing, and publishing.

**Example:**
```bash
pictova attach --site yoldaolmak --post 265713 --count 4 --engine native
```

**Options:**
- `--count [INT]`: Number of images to attach.
- `--engine native`: Highly recommended. Bypasses legacy orchestration and uses the pure, dictionary-based `execute_native_attach` pipeline.
- `--source [unsplash|semantic]`: Force a specific image source.
- `--query [STR]`: Force a search query instead of deriving it from the post context.

---

## 2. `plan`
A dry-run for discovery. Shows which images *would* be selected and to which headings they *would* be assigned, without actually downloading or processing them.

**Example:**
```bash
pictova plan --site yoldaolmak --post 265713 --count 4 --engine native
```

---

## 3. `process`
Executes discovery, download, processing, and AI metadata generation, but **stops before uploading** to WordPress. Useful for manual inspection of the `.webp` files and generated Alt texts.

**Example:**
```bash
pictova process --site yoldaolmak --post 265713 --count 2 --engine native
```

---

## 4. `review`
Quickly prints the raw WordPress post context (title, slug, excerpt, raw HTML headings) parsed by the system. Does not touch images.

**Example:**
```bash
pictova review --site yoldaolmak --post 265713
```

---

## 5. `serve`
Starts the HTTP API server to receive async job requests.

**Example:**
```bash
pictova serve --host 0.0.0.0 --port 8040
```
