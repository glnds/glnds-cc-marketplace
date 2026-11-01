# audit

Read-only repository audit: severity-ranked findings report for a local checkout.

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

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
