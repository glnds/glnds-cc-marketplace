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

## Prerequisites

- Claude Code CLI with plugin support

## Skills

### `gh-create-issue`

Create well-defined GitHub issues (single, epic, or sub-issues) with label discovery and an
optional TDD implementation plan. Superpowers-friendly.

### `gh-fix-pr-review`

Fix Claude Code Action review feedback on the current PR — both inline review threads and PR
issue comments. Picks the highest-severity unaddressed item by default, implements the fix,
commits, and replies on the review.

**Flags:** `--all`, `--skip-tests`, `--inline`, `--comments`, `--resolve`, `--dry-run`,
`--pr <number>`.

### `deep-research`

Multi-agent orchestrator that produces a long-form narrative research report (3 000–8 000 words)
grounded in the local codebase, the current web, **and** live ops evidence (CloudWatch metrics,
Logs Insights, `git log`). Dispatches six specialised subagents across a seven-phase workflow:
plan → codebase recon → user-approved outline → parallel workers (web / ops-probe / hybrid) →
single-agent synthesis → citation pass → validation. Output is written to
`./research/{date}-{slug}-report.md`.

The planner emits an **evidence-locus** (`web`, `web-grounded`, `ops`, `codebase`, `hybrid`)
alongside the shape classification, so ops-shaped queries route to the read-only `ops-probe`
subagent instead of noisy web workers. The skill is **plan-mode-aware**: when the harness is in
plan mode, `ExitPlanMode` becomes the Phase 3 approval gate instead of fighting it. A
self-disclosure block prints the tool surface before any token-expensive phase.

Not a quick-lookup tool — spends tokens deliberately (~200 K–700 K per run).

**Flags:** `--no-code` (skip codebase reconnaissance),
`--locus=web|web-grounded|ops|codebase|hybrid` (override the classifier),
`--dry-run` (stop after Phase 2), `--yes` (skip the Phase 3 approval gate outside plan mode).

### `adversarial-plan-review`

Destructive, diagnosis-only pre-flight review of an implementation plan. Designed for the seam
between Superpowers' `writing-plans` and `subagent-driven-development`. Runs as a dispatched
subagent in a fresh context with only the plan and spec paths as input — the context starvation
is what keeps the reviewer adversarial instead of sympathetic.

**Attack angles (priority-ordered):** Structural → Operational → Scope.

**Emits:** severity-tagged findings table plus a binary verdict — `PASS`, `NEEDS REWORK`, or
`NEEDS HUMAN`. No remediation, no rewrites. Findings capped at 20. One-pass-per-session rule
enforced in both `SKILL.md` and the reviewer's verdict rules so it cannot drift into a
constructive-reviewer loop.

> **⚠️ Installing the plugin is not enough.** The main agent only dispatches this skill
> automatically when a routing rule is present in your project `CLAUDE.md`. Paste the
> block below into your `CLAUDE.md`, adjusting the `docs/plans/` and `docs/specs/` paths
> to match your layout. Without the routing rule, you must invoke the skill manually
> each time.

```markdown
## Plan review routing

When `writing-plans` completes and produces a plan file in `docs/plans/`,
dispatch `adversarial-plan-review` as a subagent with only the plan path
and spec path as input, before invoking `subagent-driven-development`.

- On verdict PASS: proceed to implementation.
- On verdict NEEDS REWORK: re-invoke `writing-plans` with the findings file
  at `docs/plans/<plan>.review.md` as additional input. Do not invoke the
  review skill a second time in the same session; if the reworked plan
  still fails on next review, promote to NEEDS HUMAN.
- On verdict NEEDS HUMAN: halt and surface the review file to the user.

Skip the review entirely on plans with fewer than three tasks, or tasks
that modify a single file. The inline self-review in writing-plans already
covers those cases.
```

See [`skills/adversarial-plan-review/README.md`](./skills/adversarial-plan-review/README.md) for
the full design rationale and trade-offs.

### `code-audit`

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

See [CHANGELOG.md](./CHANGELOG.md).
