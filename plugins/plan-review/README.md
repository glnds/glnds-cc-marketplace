# plan-review

Adversarial, diagnosis-only review of implementation plans before autonomous execution.

## Installation

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
claude plugin install plan-review@glnds-cc-marketplace
```

## Skills

### `plan-review:adversarial-plan-review`

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

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
