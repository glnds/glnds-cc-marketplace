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

## Prerequisites

- Claude Code CLI with plugin support

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).
