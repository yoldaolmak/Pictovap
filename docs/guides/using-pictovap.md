# Using Pictovap

Pictovap is an open-source visual finishing engine for content publishers.
It turns unfinished articles into visually complete, rights-aware, publish-ready CMS pages.
It reads article structure, creates a Visual Brief, evaluates candidate images with Fit Scores, records Provenance Packs, generates metadata, and prepares CMS Placement instructions.

## The Pictovap Lifecycle

Pictovap automates the visual workflow through this lifecycle:

`Configure → Plan → Review → Publish`

### 1. Configure
A publisher profile defines site name, CMS type, language, output rules, filename rules, alt text rules, caption rules, and image source adapters. (See [Publisher Profile](publisher-profile.md)).

### 2. Plan
Pictovap reads an article and creates a machine-readable visual plan.
You do not need WordPress credentials to run the local demo. You do not need image provider credentials to run the local demo.

To run the local credential-free demo:
```bash
make demo
```

To plan your own article:
```bash
python -m pictova.demo --article path/to/article.md --output my-plan.json --report my-report.md
```

### 3. Review
Editors review the visual plan through a Markdown report, not raw JSON.
- **JSON output** = canonical machine-readable artifact for adapters and automation.
- **Markdown report** = editor-readable preview for humans.

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.

### 4. Publish
CMS adapters can use the plan to place selected images into WordPress or other CMS platforms. Live publishing is adapter-dependent and must be configured explicitly.

- **Connect CMS Later**: Real CMS publishing requires credentials in your `.env` file (see [WordPress Setup](wordpress-setup.md)).
- **Connect Providers Later**: Real image providers (like Openverse, Unsplash, or DepositPhotos) must be connected through image source adapters with credentials in `.env` (see [Image Sources](image-sources.md)).
