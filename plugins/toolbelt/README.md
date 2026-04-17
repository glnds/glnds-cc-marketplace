<!-- markdownlint-disable MD013 -->
# toolbelt

My collection of day-to-day tools to get the job done.

## Installation

Register the marketplace (one-time):

```text
claude plugin marketplace add glnds/claude-marketplace
```

Install the plugin:

```text
claude plugin install toolbelt@claude-marketplace
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

## Prerequisites

- Claude Code CLI with plugin support

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).
