# YOOS-VIL Coordination Contract

This file is the canonical instruction set for ongoing YOOS-VIL product work.

## Product Goal

YOOS-VIL must become a real reusable application, not a pile of one-off scripts.

It must support two simultaneous use cases:

1. Operator workflow:
   When Kemal says "attach images to post `POST_ID` with VIL", the protocol must run reliably end-to-end.
2. Reusable product workflow:
   Another user/project must be able to use the same engine with a different site profile and configuration.

## Non-Negotiable Rules

1. Do not optimize for repo appearance by breaking runtime behavior.
2. Do not delete a file if any runtime path still imports or calls it.
3. Do not report planned architecture as completed architecture.
4. Unpushed work is not done.
5. Every completed milestone must be committed and pushed.
6. Update `QWEN_STATUS.md` after each milestone with:
   - what is physically done
   - what is still planned
   - what was tested
   - what failed

## Target Product Shape

The system should be split into three layers.

### 1. Product Core

Path: `src/vil/`

This layer contains reusable business logic only.

Target modules:

- `src/vil/engine/selector.py`
- `src/vil/engine/processor.py`
- `src/vil/engine/publisher.py`
- `src/vil/engine/metadata.py`
- `src/vil/engine/quality.py`
- `src/vil/engine/gallery.py`
- `src/vil/providers/wordpress.py`
- `src/vil/profiles/yoldaolmak.py`
- `src/vil/config.py`

Responsibilities:

- select candidate images for a post
- apply image processing and filtering
- generate metadata
- upload media to WordPress
- build native gallery/image blocks
- enforce site-specific rules through profiles

### 2. App Surface

Path: `src/vil/app/`

Target modules:

- `src/vil/app/cli.py`
- `src/vil/app/api.py`
- `src/vil/app/jobs.py`
- `src/vil/app/health.py`

Responsibilities:

- CLI entrypoint
- future API surface
- background job orchestration
- structured health checks

### 3. Ops

Path: `ops/`

Only one-off or maintenance scripts belong here:

- repair scripts
- migration scripts
- indexing helpers
- diagnostics
- backfills

These are not the product surface.

## Canonical User Contract

The first stable public contract is CLI.

Target command shape:

```bash
vil attach --site yoldaolmak --post 264459
vil attach --site yoldaolmak --post 264459 --count 4 --lang tr --people-first
vil review --site yoldaolmak --post 264459
vil health
```

The engine behind `vil attach` must:

1. fetch post context
2. select relevant images
3. reject watermark / stock-feeling / wrong-language assets
4. prefer Turkish, human-centered assets when the content requires it
5. process images
6. upload media
7. attach correct blocks to the target post
8. return a structured result

## Required Structured Output

The attach pipeline should return a machine-readable result with fields like:

- `site`
- `post_id`
- `selected_assets`
- `rejected_assets`
- `uploaded_media_ids`
- `inserted_blocks`
- `warnings`
- `duration_ms`

## Current Review Findings To Respect

The current PR branch is not mergeable yet.

Verified problems:

1. `ops/yoos_vil_health.py` has a syntax error.
2. `src/core/processor.py` still imports `yo_yoldaolmak_filter`, but that file was deleted.
3. The branch uses Python 3.11 type syntax in places while this environment is currently running Python 3.9.
4. The repo cleanup removed files more aggressively than the runtime contract allows.

These must be fixed before any new cleanup wave.

## Immediate Implementation Order

### Milestone 1: Stabilize Current PR

Goal: make the PR branch runnable again before further architecture changes.

Tasks:

1. Fix syntax/runtime breakages in the existing PR branch.
2. Restore or relocate any runtime dependency that was deleted while still imported.
3. Make the branch compatible with the declared Python version strategy.
4. Run compile/import/tests and record exact results in `QWEN_STATUS.md`.

Acceptance:

- no syntax errors
- no missing imports in the canonical attach path
- tests run or failures are explicitly recorded

### Milestone 2: Define Canonical Package Layout

Goal: move from ad hoc rename-only restructuring to a coherent package.

Tasks:

1. Introduce `src/vil/` as the canonical package root.
2. Move current runtime code into `engine`, `providers`, `profiles`, `app`.
3. Keep backward-compatibility wrappers only if needed temporarily.
4. Remove dead code only after callers are updated.

Acceptance:

- one clear package root
- canonical CLI entrypoint exists
- imports resolve without relying on deleted root scripts

### Milestone 3: Ship `vil attach`

Goal: one stable operator command for real post workflows.

Tasks:

1. Implement `vil attach --site ... --post ...`
2. Support `--count`, `--lang`, `--people-first`
3. Return structured output
4. Cover the attach flow with at least one integration-style test

Acceptance:

- command exists
- command runs through the core path
- behavior is documented

### Milestone 4: Add API Surface

Goal: prepare the system to behave like a reusable app.

Tasks:

1. Add a minimal API layer, preferably FastAPI.
2. Expose a job-style endpoint for image attachment.
3. Keep API thin; business logic must remain in product core.

Acceptance:

- API wraps the same attach engine
- no duplicated business logic

## Do Not Do

- Do not invent a second parallel architecture.
- Do not hide breakages behind README claims.
- Do not delete domain-specific runtime modules just because they look messy.
- Do not merge the current PR until Milestone 1 is truly complete.

## Required Working Style

After every meaningful step:

1. update `QWEN_STATUS.md`
2. commit
3. push

If a step is only partially complete, say so clearly.
