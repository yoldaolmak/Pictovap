# Pictovap

[![CI](https://github.com/yoldaolmak/Pictovap/actions/workflows/ci.yml/badge.svg)](https://github.com/yoldaolmak/Pictovap/actions/workflows/ci.yml)

## 1. What is Pictovap?

Pictovap is an open-source visual finishing engine for content publishers.

It turns unfinished articles into visually complete, rights-aware, publish-ready CMS pages.

It reads article structure, creates a Visual Brief, evaluates candidate images with Fit Scores, records Provenance Packs, generates metadata, and prepares CMS Placement instructions.

## 2. Why it exists

Independent publishers spend significant time on visual operations per article: finding images, checking licenses, resizing, writing alt text, and placing them in a CMS. This labor scales linearly with article volume. Pictovap automates this workflow so editors can focus on narrative quality.

## 3. What problem it solves

Pictovap bridges the gap between raw written content and a visually complete CMS post. It handles the structural, visual, and metadata decisions needed to successfully place media within an article, removing the manual overhead of sourcing and placing images.

## 4. Who it is for

Pictovap is for independent publishers, editors, and developers who want to automate their visual editorial pipelines using an open-source, CLI-first approach.

Pictovap is not a writing tool.
Pictovap is not a generic AI image generator.
Pictovap is not a DAM.
Pictovap is not a stock photo search tool.
Pictovap is not a WordPress-only plugin.
Pictovap currently has no graphical UI.

It is a CLI-first open-source core for article-aware visual planning and CMS placement.

## 5. How it works

Pictovap follows a simple lifecycle: `Configure → Plan → Review → Publish`

1. **Configure**: A publisher profile defines site name, CMS type, language, output rules, filename rules, alt text rules, caption rules, and image source adapters.
2. **Plan**: Pictovap reads an article, automatically detects the article language using a deterministic local word-marker approach (falling back to the profile's configured language), extracts section excerpts for context, and creates a machine-readable visual plan with localized alt text and captions.
3. **Review**: Editors review the visual plan through a Markdown report, not raw JSON.
4. **Publish**: CMS adapters can use the plan to place selected images into WordPress or other CMS platforms. Live publishing is adapter-dependent and must be configured explicitly.

## 6. Quickstart

Get Pictovap running locally using the credential-free demo mode.

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run the local credential-free demo:

```bash
pictovap demo
```

## 7. Try your own article

You can test the demo against your own article:
```bash
pictovap plan \
  --article path/to/your/article.md \
  --profile examples/profiles/sample-publisher.yaml \
  --output my-plan.json \
  --report my-report.md
```

## 8. Outputs: JSON and editor report

- **JSON output** = canonical machine-readable artifact for adapters and automation.
- **Markdown report** = editor-readable preview for humans.

Pictovap currently has no graphical user interface. It is a CLI-first open-source core. The intended review surface is an editor-readable report, while CMS adapters consume the JSON plan.

## 9. WordPress and CMS adapters

You do not need WordPress credentials to run the local demo.

For real WordPress publishing, Pictovap will need a WordPress URL, username, and Application Password or another supported authentication method. These credentials must live in `.env` or another local secret store. They must never be committed to the repository.

The WordPress adapter should consume a CMS Placement plan. WordPress is one adapter, not the conceptual center of Pictovap.

## 10. Image source adapters

You do not need image provider credentials to run the local demo.

Current demo source: deterministic local/mock candidates.

Planned source adapters: Openverse, Unsplash, DepositPhotos, Visual Memory.

Real image providers such as Openverse, Unsplash, DepositPhotos, or private archives should be connected through image source adapters. Provider credentials must live in `.env` or another local secret store. Each selected/downloaded asset must create a Provenance Pack.

*Note: DepositPhotos and Unsplash are planned adapters, not active in the credential-free demo.*

## 11. Current status

Pictovap is an early open-source infrastructure project. It has a credential-free local demo, documented primitives, tests, and an adapter model. It does not yet claim broad ecosystem adoption, external contributors, or package downloads.

## 12. Limitations

- Only the WordPress CMS adapter is production-hardened; others are reference implementations.
- The local demo uses mock assets rather than live API calls.
- The default structural extraction handles English and Turkish articles reliably; other languages are untested.

## 13. Compatibility note

Product name: Pictovap.
Python package and legacy CLI may remain `pictova` for backward compatibility.

## 14. Contributing

See the [Documentation Portal](docs/README.md) for full guides on architecture, concepts, and contribution.
