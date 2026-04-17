#!/usr/bin/env python3
"""Verify URL liveness and DOI resolution for every source in a report's ## Sources section.

Usage: python3 verify_citations.py <report.md>

Exit codes:
    0 — all sources resolve
    1 — one or more sources dead or unresolvable (details on stderr)
    2 — file not found, unreadable, or no ## Sources section present
"""

from __future__ import annotations

import re
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

TIMEOUT = 10.0
MAX_WORKERS = 8
USER_AGENT = "deep-research-citation-verifier/1.0"

URL_RE = re.compile(r"https?://[^\s)\]>]+")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s)\]]+", re.IGNORECASE)


def extract_sources_section(text: str) -> str | None:
    match = re.search(r"^##\s+Sources\s*$(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def extract_references(sources_text: str) -> list[tuple[int, str]]:
    """Return list of (line-number-within-section, url-or-doi-uri)."""
    refs: list[tuple[int, str]] = []
    for i, line in enumerate(sources_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        url_match = URL_RE.search(stripped)
        if url_match:
            refs.append((i, url_match.group(0).rstrip(".,;")))
            continue
        doi_match = DOI_RE.search(stripped)
        if doi_match:
            refs.append((i, f"https://doi.org/{doi_match.group(0).rstrip('.,;')}"))
    return refs


def check_url(url: str) -> tuple[str, bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return url, False, f"unsupported scheme: {parsed.scheme}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT}, method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            if 200 <= status < 400:
                return url, True, f"{status}"
            # some servers return 405 for HEAD; retry GET
            if status in (403, 405, 501):
                return _check_get(url)
            return url, False, f"HTTP {status}"
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 405, 501):
            return _check_get(url)
        return url, False, f"HTTP {exc.code}"
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return url, False, f"network: {exc}"
    except Exception as exc:  # noqa: BLE001
        return url, False, f"error: {exc}"


def _check_get(url: str) -> tuple[str, bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            if 200 <= status < 400:
                return url, True, f"{status} (GET)"
            return url, False, f"HTTP {status} (GET)"
    except urllib.error.HTTPError as exc:
        return url, False, f"HTTP {exc.code} (GET)"
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return url, False, f"network (GET): {exc}"
    except Exception as exc:  # noqa: BLE001
        return url, False, f"error (GET): {exc}"


def main(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: {path} not found", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    sources = extract_sources_section(text)
    if sources is None:
        print(f"error: no '## Sources' section in {path}", file=sys.stderr)
        return 2

    refs = extract_references(sources)
    if not refs:
        print(f"warning: '## Sources' is empty or contains no URLs/DOIs", file=sys.stderr)
        return 1

    print(f"checking {len(refs)} sources from {path}...")
    failures: list[tuple[int, str, str]] = []
    successes: list[tuple[str, str]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(check_url, url): (line, url) for line, url in refs}
        for fut in as_completed(futures):
            line, url = futures[fut]
            _, ok, detail = fut.result()
            if ok:
                successes.append((url, detail))
            else:
                failures.append((line, url, detail))

    for url, detail in successes:
        print(f"  OK   {detail:<20} {url}")
    for line, url, detail in failures:
        print(f"  FAIL {detail:<20} {url} (line {line})", file=sys.stderr)

    if failures:
        print(
            f"\n{len(failures)} of {len(refs)} sources failed liveness check",
            file=sys.stderr,
        )
        return 1

    print(f"\nall {len(refs)} sources live")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: verify_citations.py <report.md>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
