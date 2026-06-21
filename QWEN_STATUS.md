# YOOS-VIL Development Status

## Current Goal
Complete Milestone 3 by turning `vil attach` into a usable operator contract on top of the canonical package root.

## Physically Completed
- Fixed `ops/yoos_vil_health.py` syntax errors so the health script parses again.
- Restored runtime modules deleted by the cleanup but still imported by the live code:
  - `yo_yoldaolmak_filter.py`
  - `yo_adaptive_filter.py`
  - `yo_unsplash.py`
- Restored `src/visual_memory/` compatibility package for ops scripts that still depend on:
  - `src.visual_memory`
  - `src.visual_memory.deposit_config`
  - `src.visual_memory.models`
- Corrected broken imports in ops scripts:
  - `ops/index_memory_daily.py`
  - `ops/index_vil.py`
  - `ops/run_deposit.py`
- Added postponed annotation evaluation where needed to stop Python 3.9 runtime failures:
  - `src/main.py`
  - `src/core/metadata_generator.py`
- Aligned packaging/runtime version declaration to Python 3.9+:
  - `pyproject.toml`
  - `docs/architecture.md`
- Fixed `src/utils/config.py` so project root resolves to repo root instead of `src/utils/`.
- Fixed `src/core/database.py` methods that were calling missing `self.execute(...)` instead of `self.db.execute(...)`.
- Replaced the broken placeholder test file with branch-accurate smoke tests for current modules.
- Added `AI_COORDINATION.md` to this branch so the active PR now carries the canonical product contract.
- Introduced `src/vil/` as the canonical package root with:
  - `src/vil/config.py`
  - `src/vil/engine/`
  - `src/vil/providers/`
  - `src/vil/profiles/`
  - `src/vil/app/`
- Added canonical CLI entrypoint: `src/vil/app/cli.py`
- Added app-surface modules:
  - `src/vil/app/jobs.py`
  - `src/vil/app/health.py`
  - `src/vil/app/api.py`
- Added `pyproject.toml` console script:
  - `vil = "src.vil.app.cli:main"`
- Updated `README.md` to show canonical `vil attach`, `vil review`, `vil health` usage.
- Removed `pytest-cov` dependency from default `pytest.ini` addopts so plain `pytest` now runs in this environment.
- Upgraded `src/vil/app/jobs.py` so `vil attach` now returns a structured contract with:
  - `command`
  - `request`
  - `post_context`
  - `constraints`
  - `selected_assets`
  - `rejected_assets`
  - `uploaded_media_ids`
  - `inserted_blocks`
  - `failed_uploads`
  - `duration_ms`
- Added post-context-based location query derivation for `semantic` attach mode when the operator only provides `--post`.
- Added structured CLI failure handling so `attach` and `review` return JSON errors instead of tracebacks.
- Added integration-style CLI contract tests in `tests/integration/test_cli_contract.py`.
- Added early attach validation in `src/vil/app/jobs.py` for:
  - missing semantic location query after derivation
  - missing Unsplash query
  - missing post_id
- Expanded `src/vil/app/api.py` from placeholder to reusable wrappers:
  - `attach_images(payload)`
  - `review_post(payload)`
  - `health_status()`
- Moved attach preparation/validation/result-normalization logic out of `src/vil/app/jobs.py` into canonical engine module:
  - `src/vil/engine/attach.py`
- Reduced `src/vil/app/jobs.py` to a thin job layer over canonical engine helpers.

## Verified
- `python3 -m compileall src tests ops yo_yoldaolmak_filter.py yo_adaptive_filter.py yo_unsplash.py` -> pass
- Import smoke check -> pass for:
  - `src.main`
  - `src.services.wordpress`
  - `src.core.filter`
  - `src.core.processor`
  - `ops.run_deposit`
  - `ops.index_vil`
  - `ops.index_memory_daily`
- Runtime filter path check -> pass:
  - `YOImageProcessor().apply_yo_filter(...)`
- `python3 -m src.vil.app.cli health` -> pass
- `python3 -m src.vil.app.cli attach --help` -> pass
- `python3 -m src.vil.app.cli review --site yoldaolmak --post 1` -> structured failure JSON when credentials are missing
- `vil attach` unsplash validation -> structured failure when query is missing
- `python3 -m pytest -q` -> pass
- `src/vil/engine/attach.py` compile/import path -> pass

## Current Test Result
- `python3 -m pytest -q`
- Status at last update: `9 passed, 1 warning`

## Planned But Not Done
- SQL injection audit and parameterized LIKE/query cleanup
- Structured logging
- Retry/error handling policy
- Full internal migration from legacy `src/main.py` / `src/core/*` modules into `src/vil/*`
- Native attach execution inside `src/vil/engine/*` instead of wrapping the legacy orchestrator
- Real HTTP API server surface (current API layer is Python-callable, not yet FastAPI/HTTP)

## Remaining Risks
- The branch now has a canonical package root, but most core logic still lives in legacy modules wrapped by `src/vil/*`.
- `vil attach` now has a structured contract, but still wraps the existing orchestrator; it is not yet a fully native `src/vil/engine/*` implementation.
- Some deleted modules were restored as compatibility modules to recover runtime behavior; they still need a proper long-term home in the planned package layout.

## Last Commands Run
```bash
python3 -m compileall src tests ops yo_yoldaolmak_filter.py yo_adaptive_filter.py yo_unsplash.py
python3 -m pytest -q
python3 -m src.vil.app.cli health
python3 -m src.vil.app.cli attach --help
python3 -m src.vil.app.cli review --site yoldaolmak --post 1
python3 - <<'PY'
import sys
sys.path.insert(0, '/Users/yoldaolmak/Projects/YOOS-VIL-pr1')
for name in ['src.main', 'src.services.wordpress', 'src.core.filter', 'src.core.processor', 'ops.run_deposit', 'ops.index_vil', 'ops.index_memory_daily']:
    __import__(name)
    print(name, 'ok')
PY
```
