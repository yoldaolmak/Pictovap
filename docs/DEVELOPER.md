# 💻 Developer Guide

Welcome to Pictova. We value clean code, strong typing, and comprehensive testing. This guide will get you up to speed with our engineering standards.

## 1. Local Setup

Pictova uses a standard Python virtual environment.

```bash
git clone <repo-url> pictova
cd pictova
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Environment Variables
Copy `.env.example` to `.env` and configure your credentials. At minimum, you need:
- `WP_USER` / `WP_PASSWORD` (App password)
- `GEMINI_API_KEY` (For the Vision Chain AI)
- `UNSPLASH_ACCESS_KEY`

## 2. Test Culture

We rely on `pytest`. We don't merge code unless all tests pass.

- **Unit Tests:** `pytest tests/unit/`
- **Integration Tests:** `pytest tests/integration/`
- **Run Everything:** `pytest tests/`

*Rule:* Mock external APIs (WordPress, Gemini) in unit tests. We test logic, not third-party uptime.

## 3. Code Standards

- **Typing:** We use strict Python type hints (`from typing import Dict, Any, List, Tuple`). Every function must have type annotations.
- **Stateless Design:** We favor pure functions over stateful classes. Keep the "Native Engine" pattern: functions take primitive Dictionaries and return primitive Dictionaries.
- **Naming:** Keep functions clear and verb-first (`build_native_metadata_map`, `execute_native_attach`).

## 4. Contributing

1. Create a feature branch (`feature/your-cool-idea`).
2. Write tests covering your feature.
3. Verify no existing tests break (`pytest tests/`).
4. Keep PRs small and focused.
