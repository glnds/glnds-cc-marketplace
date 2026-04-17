---
name: creating-github-issues
description: Use when the user asks to create one or more GitHub issues, file a ticket, open a bug report, write up a feature request, or break a plan/epic into trackable issues. Produces well-defined issues with clear requirements, the right level of detail, and (for implementation-ready issues) a TDD plan suitable for Superpowers pickup.
---

# Creating GitHub Issues

## Overview

Create well-defined GitHub issues that are ready to be picked up later, including by Superpowers
workflows. Gather clear requirements upfront and match the level of detail to the task.

The user's request (title, description, or plan text) is the input to this skill. If the skill is
invoked as a slash command, that input is passed as `$ARGUMENTS`.

**Iron rules:**

- NEVER create an issue without explicit confirmation on the summary.
- NEVER skip the Documentation phase in implementation-ready issues.
- NEVER assume detail level; ask if the input does not make it explicit.
- ALWAYS discover repository labels before drafting.
- ALWAYS flag label gaps and ask before creating new labels.
- ALWAYS include testable acceptance criteria in implementation-ready issues.
- ALWAYS ask about edge cases explicitly for implementation-ready issues.
- ALWAYS link sub-issues to their parent epic and update the epic checklist after creation.
- If requirements are vague, ask follow-up questions before proceeding.

## Step 0: Analyse the Input

Read the user's request and decide two things.

### A. Shape of the input

- **Single issue**: one focused request, bug, or improvement.
- **Multi-issue / epic**: a research document, roadmap, or plan that implies multiple deliverables.

If the input looks like a plan with multiple workstreams, ask:

> This looks like it covers multiple deliverables. Should I create:
>
> 1. An **epic** with linked sub-issues
> 2. A set of **linked issues** without a parent epic
> 3. A **single consolidated issue**
>
> And should sub-issues be created now, or only the epic with a checklist for later expansion?

### B. Detail level

- **High-level**: captures intent and value, defers implementation decisions.
- **Implementation-ready**: actionable now, with TDD plan and concrete acceptance criteria.

If the level is not clear, ask explicitly:

> Should this be a **high-level issue** (capture intent, defer details) or **implementation-ready**
> (ready to pick up and build)?

Wait for answers before proceeding.

## Step 1: Discover Repository Labels

Before drafting, run:

```bash
gh label list --limit 100 --json name,description,color
```

Then:

1. Match the issue content against existing labels (type, scope, priority, component, status).
2. Propose a set of labels that fit.
3. Identify **label gaps**: themes that have no matching label.
4. Present proposed labels and gaps to the user:

```text
## Proposed Labels
- `type:feature` (exists)
- `area:api` (exists)
- `priority:medium` (exists)

## Label Gaps
The following themes have no matching label. Would you like to create them?
- `needs-adr` for issues requiring architecture decision records
- `superpowers-ready` for issues structured for Superpowers pickup
```

If the user approves new labels, create them with `gh label create`.

## Step 2: Clarify the Request

Skip any questions already answered in the input.

### For high-level issues

1. What problem does this solve, and for whom?
2. What is the desired outcome or value?
3. What are the rough boundaries (in scope / out of scope)?
4. Are there known constraints (tech, time, dependencies)?
5. What would make this issue "ready for refinement" into an implementation-ready issue?

### For implementation-ready issues

1. What is the expected behaviour? (What should happen?)
2. What triggers this behaviour? (User action, API call, scheduled task?)
3. What are the inputs and expected outputs?
4. What is explicitly OUT of scope?
5. Are there edge cases to handle? (empty inputs, errors, limits)
6. Is this a new feature, bug fix, or improvement?
7. Are there existing patterns in the codebase to follow?
8. How do we know this is "done"? (Be specific)
9. Which documentation will need updating? (README, handbook, ADR, API docs, changelog)

### For epics / multi-issue input

1. What is the overarching goal of the epic?
2. What is the proposed breakdown into sub-issues?
3. Are there dependencies or a required order between sub-issues?
4. Which sub-issues are high-level, which are implementation-ready?

Wait for answers before proceeding.

## Step 3: Summarise Understanding

Present a summary for confirmation.

### Single issue summary

```text
## My Understanding
**Type**: [high-level | implementation-ready]
**Problem/Feature**: [one sentence]
**Expected Outcome**:
- [outcome 1]
- [outcome 2]
**Out of Scope**:
- [exclusions]
**Edge Cases** (implementation-ready only):
- [edge case]: [handling]
**Proposed Labels**: [list]
**Documentation Impact** (implementation-ready only): [files/pages to update]
```

### Epic summary

```text
## My Understanding
**Epic**: [title and one-sentence goal]
**Proposed Sub-Issues**:
1. [title] - [high-level | implementation-ready]
2. [title] - [high-level | implementation-ready]
**Dependencies**: [order or blocking relationships]
**Proposed Labels**: [list]
```

Ask: "Is this correct? Anything to add or change?"

Wait for confirmation.

## Step 4: Create the Issue(s)

Use `gh issue create` with the appropriate template below. Apply the agreed labels with `--label`.

For epics with sub-issues:

1. Create the epic first.
2. Capture its issue number.
3. Create each sub-issue with a reference to the epic (`Part of #<epic>`).
4. Update the epic body with the sub-issue checklist.

## Template A: High-Level Issue

```markdown
## Problem Statement
[What problem are we solving, and for whom?]

## Desired Outcome
[What does success look like at a high level?]

## Value / Motivation
[Why does this matter? What is the impact of not doing it?]

## Scope
**In scope:**
- [area 1]
- [area 2]

**Out of scope:**
- [explicit exclusion]

## Open Questions
- [ ] [question needing an answer before refinement]
- [ ] [question needing an answer before refinement]

## Readiness Checklist (for refinement into implementation-ready)
- [ ] Acceptance criteria defined
- [ ] Edge cases identified
- [ ] Documentation impact assessed
- [ ] Dependencies / patterns identified

## Notes
[Context, links, references, related issues]
```

## Template B: Implementation-Ready Issue

```markdown
## Problem Statement
[Clear description of what needs to be solved]

## Expected Behaviour
- When [trigger], then [outcome]
- [additional behaviours]

## Acceptance Criteria
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Specific, testable criterion 3]

## Out of Scope
- [What this issue will NOT address]

## Edge Cases
| Scenario | Expected Behaviour |
|----------|--------------------|
| [edge case] | [handling] |

## Implementation Plan (TDD)

### Phase 1: Red (Write Failing Tests)
- [ ] Test: [criterion 1 as test]
- [ ] Test: [criterion 2 as test]
- [ ] Test: [edge case 1]
- [ ] Test: [edge case 2]

### Phase 2: Green (Implement)
- Implement minimum code to pass tests
- Do not modify tests during this phase

### Phase 3: Refactor
- Clean up implementation
- Ensure all tests still pass

### Phase 4: Documentation (mandatory final step)
- [ ] [Specific doc file / handbook page / ADR to update]
- [ ] [Changelog entry if applicable]
- [ ] [README or API reference update if applicable]

## Existing Patterns to Follow
[Links to similar code, ADRs, or handbook pages]

## Notes
[Additional context, links, references]
```

## Template C: Epic

```markdown
## Epic Goal
[One-sentence overarching goal]

## Motivation
[Why this epic matters, what problem it addresses]

## Sub-Issues
- [ ] #XXX [sub-issue title] (high-level | implementation-ready)
- [ ] #XXX [sub-issue title] (high-level | implementation-ready)
- [ ] #XXX [sub-issue title] (high-level | implementation-ready)

## Dependencies / Sequencing
[Any required order or blocking relationships between sub-issues]

## Definition of Done (Epic-level)
- [ ] All sub-issues closed
- [ ] End-to-end acceptance verified
- [ ] Documentation updated across all affected areas

## Notes
[Links to source research, plans, or related work]
```

## Superpowers Compatibility

Issues produced by this skill are structured to be **Superpowers-friendly** (loose coupling, no
direct invocation):

- Acceptance criteria are concrete and testable, suitable for TDD pickup.
- The TDD plan is explicit with Red / Green / Refactor phases.
- Existing patterns are linked to help context gathering.
- Documentation is a first-class phase, not an afterthought.
- Out-of-scope is explicit, so a later Superpowers run does not overreach.

Optionally apply a `superpowers-ready` label (create it if it does not exist) to signal issues that
are structured for Superpowers pickup.
