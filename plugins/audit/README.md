# audit

Read-only repository audits: severity-ranked findings reports for a local checkout or an uploaded zip.

## Installation

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
claude plugin install audit@glnds-cc-marketplace
```

## Skills

### `audit:code-audit`

Read-only deep audit of a repository or subtree. Produces a severity-ranked Markdown report
(`audit-<slug>-<YYYYMMDD>.md`) modelled on Trail-of-Bits-style findings (Severity × Difficulty,
short- and long-term recommendations, effort estimate). Never modifies the audited project — the
only write is the report itself.

**Six dimensions (NFR priority order):** security (OWASP Top 10:2025, ASVS v5) → resilience →
cost efficiency → architecture & coupling → documentation freshness → monitoring gaps.

Falls back to ripgrep heuristics when scanners (`gitleaks`, `trivy`, `semgrep`, `osv-scanner`,
`infracost`, `checkov`) are absent.

**Flags:** `--scope=security|resilience|cost|architecture|docs|monitoring|all`.

### `audit:repo-audit`

Audit a repository uploaded as a zip archive (claude.ai chat) and produce a
Markdown findings report where each finding maps to a GitHub issue. Use `code-audit` for a
local checkout in Claude Code.

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
