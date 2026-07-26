"""Run the smallest useful contributor smoke test.

This script is intentionally narrower than the full test suite. It verifies
that a freshly installed checkout exposes the public CLI, can run the local
credential-free demo, and can produce an anonymous feedback report without
writing generated artifacts into the repository root.
"""

from __future__ import annotations

import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory


def _run(label: str, command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"{label} failed with exit code {result.returncode}\n"
            f"command: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def main() -> int:
    if find_spec("pictovap") is None:
        raise SystemExit(
            "Pictovap is not importable in this Python environment. "
            "Run `make install` inside your virtual environment first."
        )

    with TemporaryDirectory(prefix="pictovap-contributor-smoke-") as tmp:
        workspace = Path(tmp)

        version = _run(
            "version check",
            [sys.executable, "-m", "pictovap", "--version"],
            cwd=workspace,
        )
        if not version.stdout.strip().startswith("pictovap "):
            raise SystemExit(f"version check returned unexpected output: {version.stdout!r}")

        demo = _run(
            "credential-free demo",
            [sys.executable, "-m", "pictovap", "demo"],
            cwd=workspace,
        )
        if "Pictovap Local Demo" not in demo.stdout:
            raise SystemExit("demo did not print the expected Pictovap banner")

        plan_path = workspace / "sample-output.json"
        if not plan_path.exists():
            raise SystemExit("demo did not create sample-output.json in the temporary workspace")

        feedback = _run(
            "anonymous feedback report",
            [
                sys.executable,
                "-m",
                "pictovap",
                "feedback",
                "--plan",
                str(plan_path),
                "--format",
                "markdown",
            ],
            cwd=workspace,
        )
        if "Pictovap External Validation" not in feedback.stdout:
            raise SystemExit("feedback command did not print the expected Markdown summary")

    print("Contributor smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
