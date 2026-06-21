# Semantic Selection

Semantic selection is the process by which Pictova decides which images fit a given post.

## The Core Problem

A travel post about Sinop should get photos of Sinop — its harbor, its castle, its fish market. A post about packing light should get photos of backpacks and organized luggage, not tourist landmarks. This requires understanding the post's content, not just its title.

## How It Works

### Step 1: Context Derivation

Pictova reads the post from WordPress (title, excerpt, content, categories, tags) and derives a semantic context object:

- **Location query**: city, country, or region name extracted from content
- **Topic query**: the subject matter of the post (food, gear, architecture, etc.)
- **Activity hints**: verbs and activity keywords detected in the body
- **People first**: whether the post benefits from human subjects in images

### Step 2: Query Construction

The context becomes a multi-field query against the visual memory index. Pictova scores each asset across:

- `location`, `city`, `country` — geographic match
- `activity`, `scene` — contextual match
- `title`, `description`, `summary` — semantic text match
- `filename` — fallback keyword match

Assets are scored, not filtered. A photo of Sinop harbor taken from a boat scores higher than a generic harbor photo, which scores higher than an unrelated landscape.

### Step 3: Quality Gate

Scores are adjusted by the quality gate (`src/pictova/engine/quality.py`):

- Images below the blur threshold are penalized
- Images below the exposure threshold are penalized
- Face count is used when `--people-first` is active (images with faces rank higher)
- Aspect ratio is checked against target block dimensions

### Step 4: Deduplication and Ranking

Across multiple sources (Visual Memory, Unsplash, local), candidates are merged, duplicates removed by hash, and the final ranking produced. The top `--count` images pass to the processor.

## Inspecting Selection

Use `pictova plan` to see what would be selected without committing to attach:

```bash
pictova plan --site yoldaolmak --post 265713 --count 4 --people-first
```

The output shows each candidate, its source, its score, and the reason it was selected.

## Tuning Selection

Selection behavior is controlled by the site profile (`src/pictova/profiles/yoldaolmak.py`). Profile fields that affect selection:

| Field | Effect |
|-------|--------|
| `default_count` | Images per post when `--count` is omitted |
| `people_first` | Default people preference |
| `source_priority` | Ordered list of sources to query |
| `min_quality_score` | Quality gate threshold |
| `aspect_ratio` | Target ratio for block placement |
