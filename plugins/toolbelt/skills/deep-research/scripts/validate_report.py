#!/usr/bin/env python3
"""Validate a deep-research report for structure, length, and discipline.

Usage: python3 validate_report.py <report.md>

Exit codes:
    0 — all checks pass
    1 — one or more checks failed (details on stderr)
    2 — file not found or unreadable
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_H2 = ["Conclusion"]  # Executive Summary is H1, enforced via first-line check
OPTIONAL_H2 = ["Sources"]  # added by citation-agent, may not be present pre-Phase-6

MIN_WORDS = 3000
MAX_BULLET_RATIO = 0.30  # 30% of non-heading lines as bullets is the ceiling

PLAN_MODE_SIGILS = [
    r"\bTODO\b",
    r"\bNext steps\b",
    r"\bI will\b",
    r"\bI'll cover\b",
    r"\bhere'?s what I'?ll\b",
    r"\bI plan to\b",
    r"\blet me (first|start by)\b",
    r"\bwe'll need to\b",
]


def count_words(text: str) -> int:
    # strip code fences
    no_code = re.sub(r"```[\s\S]*?```", " ", text)
    # strip inline code
    no_code = re.sub(r"`[^`]*`", " ", no_code)
    # strip markdown links but keep text
    no_code = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", no_code)
    words = re.findall(r"\b\w+\b", no_code)
    return len(words)


def find_h2_sections(text: str) -> list[str]:
    return re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)


def check_bullet_ratio(text: str) -> tuple[float, int, int]:
    lines = text.splitlines()
    content_lines = [
        ln for ln in lines
        if ln.strip() and not ln.startswith("#") and not ln.startswith("```")
    ]
    if not content_lines:
        return 0.0, 0, 0
    bullet_lines = [ln for ln in content_lines if re.match(r"^\s*[-*+]\s", ln)]
    ratio = len(bullet_lines) / len(content_lines)
    return ratio, len(bullet_lines), len(content_lines)


def find_sigils(text: str) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in PLAN_MODE_SIGILS:
            if re.search(pattern, line, flags=re.IGNORECASE):
                hits.append((line.strip()[:80], lineno))
                break
    return hits


def main(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []

    # Structure: required H2 sections present
    h2s = find_h2_sections(text)
    for required in REQUIRED_H2:
        if not any(required.lower() in h.lower() for h in h2s):
            failures.append(f"missing required H2 section: '{required}'")

    # Report must start with '# Executive Summary' (prefill enforcement)
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if not re.match(r"^#\s+Executive Summary", first_line):
        failures.append(
            f"report must begin with '# Executive Summary' (got: {first_line[:60]!r})"
        )

    # Word count
    word_count = count_words(text)
    if word_count < MIN_WORDS:
        failures.append(
            f"word count {word_count} below minimum {MIN_WORDS}"
        )

    # Plan-mode sigils
    sigils = find_sigils(text)
    if sigils:
        for snippet, lineno in sigils[:5]:
            failures.append(f"plan-mode sigil at line {lineno}: {snippet!r}")
        if len(sigils) > 5:
            failures.append(f"...and {len(sigils) - 5} more plan-mode sigils")

    # Excessive bulleting
    ratio, bullets, content = check_bullet_ratio(text)
    if ratio > MAX_BULLET_RATIO:
        failures.append(
            f"bullet ratio {ratio:.1%} exceeds {MAX_BULLET_RATIO:.0%} "
            f"({bullets}/{content} non-heading lines are bullets)"
        )

    # Report
    if failures:
        print(f"FAIL: {path}", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"OK: {path} ({word_count} words, {len(h2s)} sections, {ratio:.1%} bullets)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: validate_report.py <report.md>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
