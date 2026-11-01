---
name: ship
description: Use when the user asks to ship, release, push and verify, or "get this live". Commits the current work, pushes, watches CI and the CodePipeline deploy to completion, then verifies the changed resources in production and reports evidence. Read-only on AWS; never deploys from the workstation.
argument-hint: "[commit message] [--no-commit] [--pipeline <name>]"
allowed-tools: Bash(git:*) Bash(gh:*) Bash(aws:*) Bash(mise:*) Read Grep Glob
disable-model-invocation: true
---

# ship

"Deployed" means confirmed, not assumed. This skill ends only with evidence for each stage or a
named blocker. Arguments: `$ARGUMENTS`.

## Rules

- AWS is read-only: `get-*`, `list-*`, `describe-*`, `filter-log-events`, `get-metric-data`
  only. Deploys happen through the pipeline, never from here.
- Never claim a stage passed without the command output that shows it. Never say "should be
  fine" or that something clears "later" without checking docs or live state.
- Push only to the branch the repository's `AGENTS.md` allows (trunk-based repos: the default
  branch). If it says to use PRs, stop after pushing a branch and report.

## 1. Preflight

1. Run `aws sts get-caller-identity`. The ARN must contain
   `assumed-role/AWSReservedSSO_ReadOnlyAccess`. If the token expired, stop and ask the user to
   run `aws sso login`.
2. Restate what is being shipped as a checklist (from the conversation and `git status`). Every
   item must be in the diff.

## 2. Test, commit, push

1. Run the repository's checks as bare commands (no pipes): `mise run test`, plus `mise run lint`
   if the task exists. Fix failures in the implementation, not the tests.
2. Unless `--no-commit`: commit with a conventional message (the argument, or one you derive).
3. `git push`, then confirm with `git status -sb` that the branch is no longer ahead. Note the
   SHA: `git rev-parse HEAD`.

## 3. CI

1. Find the run: `gh run list --commit <sha> --json databaseId,name,status,conclusion`.
2. Watch each one: `gh run watch <id> --exit-status`.
3. On failure, read the log (`gh run view <id> --log-failed`) and diagnose before any rerun. A
   `public.ecr.aws` rate limit is a 500 GB monthly anonymous cap: the fix is authenticated pulls,
   not a rerun.

## 4. Pipeline

1. Pipeline name: `--pipeline`, else the repository's docs or IaC, else
   `aws codepipeline list-pipelines` filtered to this repository.
2. Find the execution for the SHA: `aws codepipeline list-pipeline-executions --pipeline-name
   <name> --max-items 10`, matching `sourceRevisions[].revisionId`.
3. Poll `aws codepipeline get-pipeline-execution` until `Succeeded` or `Failed`, reporting stage
   transitions (`get-pipeline-state`). Inspect the pipeline directly; don't infer from config.

## 5. Verify live

For each resource the diff touches:

- **Lambda:** `aws lambda get-function-configuration` (memory, timeout, runtime match the IaC).
  Read the next 2-3 invocations' `REPORT` lines (`aws logs filter-log-events`): errors, duration
  versus timeout, max memory used versus memory size.
- **Alarms:** `aws cloudwatch describe-alarms --state-value ALARM`.
- **Queues:** DLQ depth (`aws sqs get-queue-attributes`, `ApproximateNumberOfMessages`).
- **After any downsizing** (memory, instance class, retention): a run at 90%+ of memory or
  timeout counts as a regression.

## 6. Report

| Stage | Evidence |
| --- | --- |
| Commit | SHA, branch, pushed |
| CI | run URL, conclusion |
| Pipeline | execution ID, final status |
| Live | per resource: what you checked and the numbers |

On a regression: prepare a revert commit, show the evidence and the revert diff, and push it only
after the user confirms.
