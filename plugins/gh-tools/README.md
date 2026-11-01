# gh-tools

GitHub workflow skills: create well-defined issues and fix PR review feedback.

## Installation

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
claude plugin install gh-tools@glnds-cc-marketplace
```

## Skills

### `gh-tools:create-issue`

Create well-defined GitHub issues (single, epic, or sub-issues) with label discovery and an
optional TDD implementation plan. Superpowers-friendly.

### `gh-tools:fix-pr-review`

Fix Claude Code Action review feedback on the current PR — both inline review threads and PR
issue comments. Picks the highest-severity unaddressed item by default, implements the fix,
commits, and replies on the review.

**Flags:** `--all`, `--skip-tests`, `--inline`, `--comments`, `--resolve`, `--dry-run`,
`--pr <number>`.

## Prerequisites

- `gh` CLI, authenticated

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
