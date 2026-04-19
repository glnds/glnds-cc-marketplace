<!-- markdownlint-disable MD013 -->
# toolbelt

My collection of day-to-day tools to get the job done.

## Installation

Register the marketplace (one-time):

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
```

Install the plugin:

```text
claude plugin install toolbelt@glnds-cc-marketplace
```

## Skills

### `gh-create-issue`

Create well-defined GitHub issues (single, epic, or sub-issues) with labels and an optional TDD
implementation plan. Superpowers-friendly.

### `gh-fix-pr-review`

Fix Claude Code Action review feedback on the current PR — both inline threads and PR issue
comments, with severity-based prioritisation and auto-reply. Supports `--all`, `--skip-tests`,
`--inline`, `--comments`, `--resolve`, `--dry-run`, and `--pr <number>`.

### `deep-research`

Multi-agent orchestrator that produces a long-form narrative research report (3000-8000 words)
grounded in the local codebase AND the current web. Dispatches 5 specialised subagents across a
7-phase workflow (plan → codebase recon → user-approved outline → parallel web workers → single
synthesis → citation pass → validation). Output written to `./research/{date}-{slug}-report.md`.
Not for quick lookups — spends tokens deliberately (~200K-700K per run). Optional flag:
`--no-code` to skip codebase reconnaissance.

### `adversarial-plan-review`

Destructive, diagnosis-only pre-flight review of an implementation plan, built for the seam
between Superpowers' `writing-plans` and `subagent-driven-development`. Runs as a dispatched
subagent in a fresh context with only the plan and spec paths as input — the context starvation
is what keeps the reviewer adversarial instead of sympathetic. Applies three priority-ordered
attack angles (Structural → Operational → Scope) and emits a severity-tagged findings table plus
a binary verdict: `PASS`, `NEEDS REWORK`, or `NEEDS HUMAN`. No remediation, no rewrites, findings
capped at 20. One-pass-per-session rule enforced in both `SKILL.md` and the reviewer's verdict
rules so it cannot drift into a constructive-reviewer loop. See the skill's README for the
ready-to-paste CLAUDE.md routing block.

### `code-audit`

Read-only deep audit of a repository or subtree. Produces a severity-ranked Markdown report
(`audit-<slug>-<YYYYMMDD>.md`) modelled on Trail-of-Bits-style findings (Severity × Difficulty,
short/long-term recommendations, effort estimate). Six dimensions in NFR priority order: security
(OWASP Top 10:2025, ASVS v5) → resilience → cost efficiency → architecture & coupling →
documentation freshness → monitoring gaps. Never modifies the audited project — the only write is
the report itself. Falls back to ripgrep heuristics when scanners (`gitleaks`, `trivy`, `semgrep`,
`osv-scanner`, `infracost`, `checkov`) are absent. Optional flag:
`--scope=security|resilience|cost|architecture|docs|monitoring|all`.

## Prerequisites

- Claude Code CLI with plugin support

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).
