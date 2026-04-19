<!-- markdownlint-disable MD013 MD040 -->
# Adversarial plan review

A Superpowers-compatible Claude Code skill that runs a destructive, diagnosis-only review of an implementation plan between `writing-plans` and `subagent-driven-development`. It surfaces failure modes the existing inline checklists structurally cannot see: hidden coupling, operational failure paths, and scope drift. It emits severity-tagged findings and a binary verdict. It does not propose fixes. It does not rewrite. It does not iterate.

## What this is

The skill is a single review step that sits in one specific seam of the Superpowers workflow. You invoke it once after a plan is written and before implementation starts. It dispatches a fresh subagent that reads only the plan and the spec, applies a priority-ordered attack checklist, and returns one of three verdicts: proceed, rework, or halt. Everything about the skill's design (single pass, fresh context, no remediation, capped findings, binary verdict) exists to preserve that narrow role and prevent it from drifting into a second constructive reviewer, which the upstream project has already measured as net-negative on quality per unit time.

## The gap this fills

Superpowers performs constructive review at both ends of its workflow. `brainstorming` ends with a self-check for placeholders, contradictions, ambiguity, and scope. `writing-plans` ends with its own inline self-review for spec coverage, placeholder scans, and type consistency. `subagent-driven-development` runs an explicitly adversarial reviewer after each task is implemented. All three existing checks share a property: they ask "is anything missing?" or "does this match the spec?". None of them asks "what will break at 3am when task 5 fails after task 4 committed?".

That last question is what this skill exists to answer.

The empirical case for this exact shape comes from the Superpowers project itself. In the v5.0.6 release notes (25 March 2026), Jesse Vincent published regression testing data across five versions with five trials each, and found that the dispatched subagent review loop he had previously added between plan writing and execution doubled execution time by roughly 25 minutes without measurably improving plan quality, while a 30-second inline checklist caught 3 to 5 real bugs per run with comparable defect rates. He replaced the subagent loop with the inline check. Open issue [obra/superpowers#1130](https://github.com/obra/superpowers/issues/1130) (11 April 2026, unclaimed) names the reason the subagent loop failed and the shape of the layer that would actually earn its cost: a *destructive* reviewer that does diagnosis only, with three named attack angles, and no fix suggestions. That framing is what this skill implements.

The short version: if you add a reviewer that does the same job as the inline checklist, you pay the cost without getting new findings. If you add a reviewer that asks a different question (what breaks, not what is missing), you get findings the inline check structurally cannot produce.

## How it works

The flow is a three-state decision tree with one external entry point and three exit points.

```
writing-plans (Superpowers)
        │
        ▼
adversarial-plan-review  ◄──── (this skill)
        │
        ├── VERDICT: PASS           ──► subagent-driven-development
        ├── VERDICT: NEEDS REWORK   ──► re-invoke writing-plans with findings
        └── VERDICT: NEEDS HUMAN    ──► halt, surface review to user
```

The reviewer runs as a dispatched subagent in a fresh context window. That isolation is load-bearing: Superpowers' v5.0.2 release notes document that reviewers which inherit the planner's context drift into the developer role and lose adversarial posture. The only inputs passed into the subagent are the path to the plan file and the path to the spec file. No session summary, no task list, no previous findings. Context starvation is the mechanism that keeps the reviewer destructive.

Once invoked, the subagent loads both files, applies the prompt in `review-prompt.md` verbatim, and emits a markdown findings table plus a single verdict line. The findings are also written to `docs/plans/<plan>.review.md` for audit. The main agent reads the verdict and takes one of the three actions above without arguing with the reviewer's output.

The reviewer works through three attack angles in priority order:

1. **Structural**: hidden coupling, load-bearing assumptions, irreversible decisions dressed as reversible, type and signature drift, undefined references, missing interface contracts.
2. **Operational**: failure at 3am, recovery when one task commits and the next dies, rollback granularity, idempotency, missing preconditions.
3. **Scope**: where "simple" grows, hidden dependencies, scope not bounded by acceptance criteria, missing non-goals.

Priority ordering is mandatory. Without it, LLM reviewers front-load easy observations (naming, formatting) and miss the deeper issues. The pattern comes from [richiethomas/claude-devils-advocate](https://github.com/richiethomas/claude-devils-advocate) and is consistent across every adversarial review skill that works in practice.

## Installation

The skill is a directory with two files. Drop it into your Claude Code skills folder:

```
~/.claude/skills/adversarial-plan-review/
├── SKILL.md          # skill metadata and invocation contract
├── review-prompt.md  # the prompt the subagent applies verbatim
└── README.md         # this file
```

If you use Superpowers via its plugin layout, the same files belong under `~/.claude/plugins/superpowers/skills/adversarial-plan-review/` instead, so that `using-superpowers` discovers it alongside the built-in skills.

After copying the files, add the routing rule from the CLAUDE.md integration block in `SKILL.md` to your project `CLAUDE.md`. The routing rule is what makes the main agent invoke the skill automatically at the right moment in the workflow. Without the routing rule the skill is still usable, but you have to trigger it manually with `use the adversarial-plan-review skill on docs/plans/foo.md against docs/specs/bar.md`.

## When to use, when to skip

Use it on:

- Plans with three or more tasks
- Plans that span multiple services or repositories
- Plans that introduce new dependencies, new infrastructure, or new external integrations
- Plans that rely on sequential commits (where one task commits and a later task builds on that commit)
- Plans where a mid-run failure would require manual recovery rather than a clean retry

Skip it on:

- Single-file or single-task plans (the inline self-review in `writing-plans` already covers these, and the subagent cost is unjustified)
- Cosmetic changes, formatting sweeps, documentation-only changes
- Plans that have already failed this review once in the same session (see "Trade-offs" below for why rerunning is a trap)

The rule of thumb: if a mid-run failure would cost you more than 15 minutes of manual recovery, the review is worth its cost. If recovery is "git reset and try again", it is not.

## Output anatomy

A typical output on a plan with real issues looks like this:

```markdown
# Adversarial review: add-oauth-google

## Findings

| ID | Severity | Dimension   | Failure scenario                                                                                                                                              | Evidence |
|----|----------|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| S1 | CRITICAL | Structural  | Task 4 modifies the session schema; task 6 reads session.user_id which does not exist until task 4 runs. If task ordering shifts, task 6 fails at runtime.   | "Task 6: add user profile endpoint using session.user_id" |
| O1 | HIGH     | Operational | GOOGLE_CLIENT_SECRET is read in task 3 but never listed as a required env var. Agent will stall in interactive prompt mid-implementation.                     | "Task 3: initialize Google OAuth client" |
| C1 | MEDIUM   | Scope       | Task 7 says "and update any existing tests that depend on the old session format." Unbounded scope: affected test count is not enumerated.                   | "Task 7: update session tests" |

VERDICT: NEEDS REWORK
```

On a sound plan, the output is a two-line document:

```markdown
# Adversarial review: refactor-logger

## Findings

VERDICT: PASS
```

An empty findings table plus `VERDICT: PASS` is the expected outcome for well-constructed plans, not a failure of the reviewer. If you never see a PASS verdict, the reviewer is miscalibrated.

## Trade-offs and limits

**Cost.** The reviewer runs one subagent pass with input of roughly the plan plus the spec (typically 20 to 60k tokens) and output of a few thousand tokens. On a multi-task plan this is cheap compared to the cost of the implementation run it protects. On a trivial plan, it is waste. The `when_not_to_use` rule in `SKILL.md` and the routing rule in CLAUDE.md both exist to prevent that waste.

**Time.** The skill's budget ceiling is roughly 2x the inline self-review of `writing-plans`. In practice this lands around 1 to 3 minutes for a typical plan, not the 25 minutes of the v5.0.6-era subagent loop. The difference is that this skill is a single pass with a different question, not an iterative loop replicating the inline check.

**Rerun trap.** The skill enforces a one-pass-per-session rule. If the first review returns NEEDS REWORK and the plan is reworked, running the review a second time on the reworked plan tends to drift: the main agent has implicit context from the rework cycle that leaks through file paths and naming, and the reviewer gets softer with each pass. The rule is: one review, act on the verdict, and if the reworked plan fails on a second review (in a future session) promote straight to NEEDS HUMAN. Do not build a loop.

**Sycophancy.** The most common failure mode of LLM reviewers is conceding under pushback. This skill side-steps it by making the output an artifact (a file on disk), not a conversation turn. The main agent reads the verdict and acts on it. There is no dialog with the reviewer to concede in.

**Known blind spots.** The reviewer does not execute code or fetch dependencies. It cannot detect failure modes that require runtime information: rate limits on external APIs, actual latency of service calls, real-world dataset characteristics. For those failure modes, the post-task adversarial review in `subagent-driven-development` is the correct layer, not this one.

## Related work and attribution

The design draws on four patterns from the Claude Code ecosystem:

- [obra/superpowers#1130](https://github.com/obra/superpowers/issues/1130) names the gap and the three-angle attack model this skill implements.
- [github/spec-kit](https://github.com/github/spec-kit) `/speckit.analyze` provides the template for severity-tagged findings with stable IDs and a capped finding count.
- [aaddrick/contrarian](https://github.com/aaddrick/contrarian) is the best verbatim adversarial subagent in the ecosystem; the "no fix suggestions, diagnosis only" rule comes from its Tenth Man framing.
- [richiethomas/claude-devils-advocate](https://github.com/richiethomas/claude-devils-advocate) establishes priority-ordered review as the mechanism that keeps LLM reviewers from front-loading easy observations.

The empirical basis for the single-pass design is Jesse Vincent's v5.0.6 regression data in the Superpowers [release notes](https://github.com/obra/superpowers/blob/main/RELEASE-NOTES.md).
