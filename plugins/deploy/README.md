# deploy

Ship and verify: commit, push, watch CI and CodePipeline, check the live resources, report evidence.

## Installation

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
claude plugin install deploy@glnds-cc-marketplace
```

## Skills

### `deploy:ship`

Run `/deploy:ship [commit message]` when the work is ready. It checks the read-only SSO identity,
runs the repository's mise test and lint tasks, commits and pushes, watches the GitHub Actions run
and the CodePipeline execution for that SHA, then verifies each changed resource live (Lambda
config and next invocations, alarms, DLQ depth) and reports an evidence table. AWS access is
read-only; a regression gets a prepared revert that is pushed only after you confirm.

**Flags:** `--no-commit` (ship what is already committed), `--pipeline <name>`.

## Prerequisites

- `gh` CLI, authenticated
- AWS CLI with a read-only SSO profile (`AWSReservedSSO_ReadOnlyAccess`)

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
