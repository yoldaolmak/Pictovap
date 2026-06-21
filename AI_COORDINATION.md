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

### 2. App Surface

Path: `src/vil/app/`

Target modules:

- `src/vil/app/cli.py`
- `src/vil/app/api.py`
- `src/vil/app/jobs.py`
- `src/vil/app/health.py`

### 3. Ops

Path: `ops/`

Only one-off or maintenance scripts belong here.
