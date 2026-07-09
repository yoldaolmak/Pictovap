"""
Public-language guard test.

Ensures public-facing documentation does not contain forbidden phrases
that would make the repository look like it was prepared for a specific
external program, grant, or approval process.

This guard scans only public-facing documentation files, NOT source code
(which may legitimately reference provider names in adapter implementations).
"""

import os
import re
import pytest

# Root of the repository
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FORBIDDEN_PHRASES = [
    "Claude",
    "Anthropic",
    "claude-for-oss",
    "Claude for OSS",
    "application readiness",
    "guaranteed acceptance",
    "qualification",
    "program thresholds",
]

# Compile a single regex for efficiency — case-sensitive match
FORBIDDEN_PATTERN = re.compile("|".join(re.escape(phrase) for phrase in FORBIDDEN_PHRASES))

# Public-facing documentation paths (relative to repo root)
PUBLIC_DOC_PATHS = [
    "README.md",
    "docs",
    "CHANGELOG.md",
    "ROADMAP.md",
    "examples",
    "CONTRIBUTING.md",
]


def _collect_markdown_files():
    """Collect all markdown files under the public-facing paths."""
    files = []
    for rel_path in PUBLIC_DOC_PATHS:
        abs_path = os.path.join(REPO_ROOT, rel_path)
        if os.path.isfile(abs_path):
            files.append(abs_path)
        elif os.path.isdir(abs_path):
            for dirpath, _dirnames, filenames in os.walk(abs_path):
                for fname in filenames:
                    if fname.endswith(".md"):
                        files.append(os.path.join(dirpath, fname))
    return files


def _scan_file(filepath):
    """Return list of (line_number, line_text, matched_phrase) tuples."""
    violations = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            match = FORBIDDEN_PATTERN.search(line)
            if match:
                violations.append((line_number, line.strip(), match.group()))
    return violations


def test_no_forbidden_phrases_in_public_docs():
    """Public-facing docs must not contain forbidden program-specific phrases."""
    md_files = _collect_markdown_files()
    assert md_files, "No markdown files found to scan — check PUBLIC_DOC_PATHS"

    all_violations = {}
    for filepath in md_files:
        violations = _scan_file(filepath)
        if violations:
            rel = os.path.relpath(filepath, REPO_ROOT)
            all_violations[rel] = violations

    if all_violations:
        report_lines = ["Forbidden phrases found in public documentation:\n"]
        for path, violations in sorted(all_violations.items()):
            for line_num, line_text, phrase in violations:
                report_lines.append(f"  {path}:{line_num}  phrase={phrase!r}")
                report_lines.append(f"    {line_text}")
        report = "\n".join(report_lines)
        pytest.fail(report)
