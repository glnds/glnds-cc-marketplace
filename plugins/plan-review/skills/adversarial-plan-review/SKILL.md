---
name: adversarial-plan-review
description: Destructive, diagnosis-only pre-flight review of an implementation plan. Runs as a dispatched subagent with fresh context between writing-plans and subagent-driven-development. Surfaces failure modes the inline plan-writing checklists structurally cannot see, emits severity-tagged findings and a binary verdict. No remediation, no rewrites, no second pass.
when_to_use: After writing-plans completes and before subagent-driven-development starts. Multi-task plans (3+ tasks), plans that span multiple services or introduce new dependencies, plans that rely on sequential commits, any plan where a mid-run failure would require manual recovery.
when_not_to_use: "Single-file or single-task plans (the inline self-review in writing-plans already suffices). Plans that have already failed this review once in the same session (re-running yields diminishing returns: if the second pass fails, the plan needs human reshaping, not more review)."
---
<!-- markdownlint-disable MD013 MD040 -->

# Adversarial plan review

Superpowers performs constructive review at both ends of the workflow: `brainstorming` and `writing-plans` each end with an inline self-check, and `subagent-driven-development` includes an adversarial reviewer, but only *after* each task is implemented. This skill fills the specific gap between `writing-plans` completing and `subagent-driven-development` starting: destructive, diagnosis-only review of the plan itself, before any code is written.

The scope is deliberately narrow. This skill does not improve the plan. It does not propose fixes. It does not rewrite sections. It finds reasons the plan will fail during autonomous implementation and reports them. Anything beyond that duplicates what `writing-plans` already does, and the v5.0.6 regression data shows that a second constructive reviewer on top of existing constructive reviewers has negative ROI.

## Invocation contract

Dispatch this skill as a subagent in a fresh context. Context inheritance is the documented failure mode (Superpowers v5.0.2 release notes): reviewers that inherit the planner's context role-play as the developer and lose adversarial posture.

Pass exactly two inputs to the subagent:

1. Path to the plan file (for example, `docs/plans/<plan>.md`)
2. Path to the spec file (for example, `docs/specs/<spec>.md`)

Pass nothing else. No session summary, no task list, no previous review findings, no CLAUDE.md excerpts. The context starvation is what keeps the reviewer adversarial instead of sympathetic.

The subagent's task is to load both files, apply `review-prompt.md` from this skill directory verbatim, and emit findings to stdout and to `docs/plans/<plan>.review.md` for audit.

## Review procedure

The reviewer applies three attack angles, priority-ordered. Priority ordering is mandatory: without it, LLM reviewers front-load easy observations (naming, formatting) and miss the deeper issues.

1. **Structural**: hidden coupling between tasks, load-bearing assumptions not written down, irreversible decisions dressed as reversible, type and signature drift between tasks, undefined references, missing interface contracts, files two tasks both modify without coordination.
2. **Operational**: failure at 3am, recovery when task N commits and task N+1 dies, rollback plan presence and granularity, idempotency per task, loss of context mid-task, missing preconditions (env vars, credentials, service availability, migrations that must precede code changes).
3. **Scope**: where "simple" grows, hidden dependencies, the second system inside the first, tasks that silently pull in unrelated refactors, scope not bounded by the acceptance criteria, missing non-goals section.

Exhaust Structural before Operational. Exhaust Operational before Scope. Within a dimension, emit the most severe findings first.

## Output format

The subagent emits a single markdown document:

```
# Adversarial review: <plan name>

## Findings

| ID | Severity | Dimension | Failure scenario | Evidence |
|----|----------|-----------|------------------|----------|
| S1 | CRITICAL | Structural | <one or two concrete sentences> | <quoted plan/spec text> |
| O1 | HIGH     | Operational | ... | ... |

VERDICT: PASS | NEEDS REWORK | NEEDS HUMAN
```

Cap total findings at 20. If the reviewer would emit more, the plan is not salvageable through review and the verdict is automatically NEEDS HUMAN, with the 20 most severe findings listed to support the escalation.

## Verdict rules

The verdict is binary in outcome (proceed, rework, or halt):

- **PASS**: no CRITICAL findings, fewer than two HIGH findings. The main agent proceeds to `subagent-driven-development`.
- **NEEDS REWORK**: any CRITICAL finding, or two or more HIGH findings. The main agent re-invokes `writing-plans` with the review findings file as additional input.
- **NEEDS HUMAN**: structural ambiguity that cannot be resolved from plan and spec alone (the spec contradicts itself, the plan assumes infrastructure that is not defined anywhere, or the finding count exceeds 20). The main agent halts and surfaces the review file to the user.

Do not emit a fourth verdict. Do not emit conditional verdicts ("PASS if you change X").

## Hard rules for the reviewer

- Diagnosis only. No fix suggestions. No rewrites.
- No LOW severity. If it is not CRITICAL, HIGH, or MEDIUM, do not emit it.
- No style, naming, or formatting findings.
- No findings that cannot be tied to a concrete failure scenario during autonomous implementation.
- One pass. No iteration loop with the reviewer. If NEEDS REWORK fires twice on the same plan within the same session, the second outcome is automatically promoted to NEEDS HUMAN.
- Fire and forget. The main agent does not argue with the verdict. It reads the verdict and acts on it.

## Budget

Time-box to roughly 2x the inline self-review step of `writing-plans`. If the reviewer runs longer, terminate and fall back to the existing inline review. Jesse Vincent's v5.0.6 regression data establishes the ceiling: any reviewer that costs more than ~25 minutes per run without measurably improving plan quality has negative ROI. This skill stays well under that ceiling because it is a single pass, a single subagent, diagnosis only.

## CLAUDE.md integration

Add this routing rule to the project CLAUDE.md so the main agent invokes the skill automatically:

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
