# Claude for Open Source — Readiness Assessment

This document is an honest internal assessment of Pictovap's readiness for the Claude for Open Source program. It does not claim qualification.

## What Pictovap Is

Pictovap is an open-source visual finishing engine for content publishers. It reads article structure, creates a visual brief, evaluates candidate images, records provenance, generates metadata, and produces CMS placement instructions.

It addresses the gap between "article text is written" and "page is visually complete and publish-ready."

## What OSS Gap It Fills

Existing tools solve parts of the visual publishing problem:
- Stock photo APIs find images but do not understand article context.
- DAM systems store assets but do not place them.
- SEO plugins generate metadata but do not select images.
- WordPress media uploaders handle files but do not evaluate fit.

No existing open-source project provides the full article-aware visual finishing workflow: analysis → selection → provenance → placement.

## Why Independent Publishers Need This

Independent publishers spend significant time on visual operations per article. This labor scales linearly with article volume. Pictovap aims to reduce it to a single pipeline invocation.

## What Currently Works

- Four core primitives as Python dataclasses: VisualBrief, FitScore, ProvenancePack, CMSPlacement
- Local credential-free demo producing a complete pipeline output
- WordPress/Gutenberg CMS adapter (production-tested)
- Image source adapters for local files, Unsplash, DepositPhotos, Visual Memory DB
- AI metadata generation via Gemini, Claude CLI, LM Studio fallback chain
- Publisher profile configuration model
- Unit tests for all four primitives
- Adapter architecture with documented extension points

## What Is Still Early

- Core primitives recently extracted; internal engine still passes dicts in places
- Local demo uses mock data rather than real image processing
- Only WordPress has a production-tested adapter; Ghost and Strapi are stubs
- FitScore is rule-based with hardcoded weights, not yet configurable per profile
- Publisher profiles exist as Python dataclasses but not yet loadable from YAML

## What External Contributors Can Build

- Image source adapters: Openverse, Pexels, Pixabay, Wikimedia Commons
- CMS adapters: Ghost, Strapi, Hugo, Contentful
- Publisher profiles: Example configurations for different publisher types
- Scoring extensions: Custom FitScore dimensions
- Documentation: Tutorials, adapter guides, translations
- Tests: Coverage for engine modules, edge cases

## Current Evidence

- Public MIT-licensed repository on GitHub
- Working local demo with no credential requirements
- Documented primitives with unit tests
- Real-world dogfooding on yoldaolmak.com
- Adapter architecture with documented extension points
- Issue templates and contribution guide
- Honest roadmap without SaaS promises

## Evidence Still Needed

- External contributors beyond the original author
- Usage by at least one non-yoldaolmak publisher
- Published package on PyPI with download metrics
- Dependent projects or integrations
- Tagged releases with semantic versioning
- OpenSSF Scorecard improvements
- Community engagement from external users
- Case studies from non-travel publishers
