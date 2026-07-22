# Your First Adapter Pull Request

This is the shortest supported path from an available Pictovap issue to a
reviewable pull request. Choose one route before writing code.

## Choose a route

| If you are building... | Use this route |
| --- | --- |
| A small, broadly useful integration maintained with Pictovap | In-tree adapter |
| An integration with its own dependencies or release cadence | Standalone plugin |

For the current contributor sprint, claim an available issue first. A claim
keeps two people from solving the same adapter and lets the maintainer confirm
credentials, attribution, and acceptance criteria before implementation.

The project requires Python 3.10 or newer. If `python3 --version` reports an
older system interpreter, create the environment with an installed Python 3.10+
binary (for example, `python3.11`).

## In-tree adapter

Use this route for an adapter that belongs in the Pictovap repository.

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
make install
make contribution-check
```

Then copy the closest reference implementation:

- A key-free image provider: `src/pictovap/providers/openverse.py`
- A credentialed image provider: `src/pictovap/providers/pexels.py`
- An API-backed CMS adapter: `src/pictovap/publishers/ghost.py`
- A filesystem CMS adapter: `examples/adapters/custom_cms_adapter.py`

Your pull request is ready when it includes an adapter, mocked tests, any
needed documentation, and a passing `pytest tests/unit -q` run.

## Standalone plugin

Use this route when the adapter should be published and versioned separately.

```bash
pip install pictovap
pictovap scaffold provider your-adapter
cd pictovap-your-adapter
```

The generated `CONTRIBUTING.md` contains the exact development, contract, and
runtime-verification commands for that package. The scaffold is intentionally
small: replace one adapter class and its test fixture rather than learning the
entire Pictovap source tree.

## Before opening a pull request

Use this checklist in the PR description:

- [ ] The adapter has no hardcoded credentials.
- [ ] HTTP or CMS calls are mocked in tests.
- [ ] `pictovap.testing` contract helpers pass.
- [ ] Provider candidates include licensing and attribution fields, or CMS
      results include `placed`, `failed`, and `warnings`.
- [ ] The relevant runtime path was checked: `doctor`, provider `plan`, or CMS
      `publish --dry-run`.

If one of these requirements is unclear, ask on the issue before implementing.
That is a normal contribution checkpoint, not a failure.
