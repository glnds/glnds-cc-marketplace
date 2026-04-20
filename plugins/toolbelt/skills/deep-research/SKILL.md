---
name: deep-research
description: Use when the user asks for research, an audit, a migration analysis, a library comparison, a CVE impact assessment, a technology evaluation, or any question that requires local codebase context, current web sources, or live ops/metric evidence (CloudWatch, git log). Produces a long-form narrative report (3000-8000 words) written to disk. NOT for quick lookups — this spends tokens deliberately. Triggers on phrases like "research X", "audit Y", "how does recent X affect us", "compare A vs B", "investigate", "investigate a metric spike", "explain a duration / latency / cost delta", "compare behaviour between two dates", "correlate a regression with a deploy".
argument-hint: [research topic or question] [--no-code] [--locus=web|web-grounded|ops|codebase|hybrid] [--dry-run] [--yes]
allowed-tools: Agent Bash Read Write Glob Grep WebSearch WebFetch
disable-model-invocation: true
---

# deep-research

Orchestrator that produces a long-form narrative research report grounded in this codebase AND the
current web. Implements Anthropic's orchestrator-worker pattern with a codebase-reconnaissance phase
prepended so the report names your actual files, versions, and usage sites — not generic summaries.

Topic: `$ARGUMENTS`

## Flags

- `--no-code` — skip Phase 2 codebase reconnaissance. Use only when the query is demonstrably
  external (CVE roundups, vendor-neutral comparisons). When in doubt, keep recon on.
- `--locus=web|web-grounded|ops|codebase|hybrid` — override the evidence-locus classifier. The
  planner otherwise picks a locus from the six axes in `references/methodology.md`; use this
  when you already know where the evidence lives and want to skip the classifier's judgement.
- `--dry-run` — stop the run after Phase 2. Produces `plan.md` and `recon.md`, prints the
  summary, and exits without dispatching Phase 4. Same "see before you commit" guarantee that
  plan mode provides, usable outside plan mode.
- `--yes` — skip the Phase 3 approval gate when running outside plan mode. Still prints the
  Self-disclosure block, still runs Phases 1–2, but does not wait for user approval before
  dispatching Phase 4. Inside plan mode this flag has no effect — `ExitPlanMode` is the gate.

## Self-disclosure

Print the relevant block verbatim before doing anything else in the run. The block depends on
whether the harness is in plan mode (detected via the `Plan mode is active` system-reminder in
the orchestrator's own session context).

**Moment 1 — plan mode active.** Written into the harness-assigned plan file alongside the
research outline at the end of Phase 2:

```text
deep-research is running inside **plan mode**.

Tool access right now (read-only):
  Read, Grep, Glob, WebSearch, WebFetch, Bash (read-only only)

What happens in plan mode:
  Phase 1 (planner)  — read-only. Produces plan.md.
  Phase 2 (recon)    — read-only. Produces recon.md.
  Phase 3 (approval) — I write the plan + recon summary into this file,
                       then call ExitPlanMode. You review and approve
                       or reject there.

What happens AFTER you approve via ExitPlanMode:
  Plan mode ends. Phase 4 workers dispatch with the following tool surface:
    • locus=web      → WebSearch, WebFetch (read-only from the internet)
    • locus=ops      → Bash constrained to read-only AWS CLI + git log + Read
    • locus=codebase → Read, Grep, Glob only
  Phase 5 (synthesis) writes {report}.md to disk.
  Phase 6 (citations) edits {report}.md in place.

If you want to keep everything read-only, reject the plan — the skill
will stop after Phase 2.
```

**Moment 2 — plan mode inactive.** Printed to chat before Phase 1:

```text
deep-research is running **outside plan mode** (auto mode / default).

Tool access the skill and its workers will use:
  Orchestrator:     Agent, Bash, Read, Write, Glob, Grep, WebSearch, WebFetch
  Web worker:       WebSearch, WebFetch, Read, Write
  Ops-probe worker: Bash (read-only allowlist), Read, Grep, Write
  Code-recon:       Read, Glob, Grep, Bash (read-only), Write
  Synthesizer:      Read, Write, WebFetch
  Citation-agent:   Read, Edit, WebFetch, Bash (read-only)

Phase 3 will still ask for your approval before Phase 4 burns tokens.
To skip the approval gate, pass --yes.
```

## Core contract

- **Narrative prose, not bullets.** Target 3000-8000 words in flowing paragraphs. Written to disk.
- **Grounded in THIS codebase.** Phase 2 recon brief is passed verbatim to every web worker.
- **Parallel retrieval, serial synthesis.** 3-5 workers fan out; one agent writes the final report.
- **Citations are post-hoc.** Synthesizer writes clean prose; citation-agent attributes claims after.
- **Orchestrator never holds raw content.** Subagents write to files; orchestrator reads paths.

## Architecture

This skill runs as the main session and dispatches 6 subagents via the Agent tool:

| Phase | Subagent                        | Model   | Parallelism       |
| ----- | ------------------------------- | ------- | ----------------- |
| 1     | `toolbelt:research-planner`     | inherit | 1                 |
| 2     | `toolbelt:code-reconnaissance`  | haiku   | 1                 |
| 4     | `toolbelt:research-worker`      | sonnet  | **N in parallel** |
| 4     | `toolbelt:ops-probe`            | sonnet  | **N in parallel** |
| 5     | `toolbelt:research-synthesizer` | opus    | 1 (serial)        |
| 6     | `toolbelt:citation-agent`       | haiku   | 1                 |

Phase 4 dispatches `research-worker`, `ops-probe`, or one of each depending on
`evidence_locus`. The synthesizer is indifferent — both worker types write the same
`worker-{N}.md` with a trailing `Status: COMPLETE` sigil.

Subagents cannot spawn subagents — only this orchestrator fans out. Parallel section-writing in
Phase 5 produces disjointed reports; single-agent synthesis is deliberate.

## Setup

Derive:

```text
run-id   = {YYYY-MM-DD}-{kebab-slug-of-topic}   # e.g. 2026-04-17-aws-sdk-cve-impact
run-dir  = ./research/{run-id}/
report   = ./research/{run-id}-report.md
```

Create `run-dir` with `Bash mkdir -p`. If CWD is read-only, fall back to
`~/Documents/claude-research/{run-id}/`.

## Plan-mode adapter

The harness may already be in plan mode when the skill is invoked. Plan mode is designed for
implementation approval and forces the turn to end with `ExitPlanMode`; its description
explicitly says *"do NOT use this tool for research tasks"*. Without an adapter, the skill's
Phase 3 approval prompt fights the harness.

**Detection.** On entry, inspect the orchestrator's own session context for a
`Plan mode is active` system-reminder. If present, plan mode is active.

**Behaviour when active:**

1. Treat the harness-assigned plan file path as the home of `{run-dir}/plan.md`. Every other
   artefact (`recon.md`, `worker-*.md`, final report) still lives under `{run-dir}/` — only the
   plan file is relocated.
2. Run Phase 1 (planner) and Phase 2 (recon) unchanged. Both are read-only and plan-mode-legal.
3. Write Phase 1 output + Phase 2 summary + the `evidence_locus: …` decision + the proposed
   worker roster + the Self-disclosure Moment 1 block into the harness-assigned plan file.
4. Call `ExitPlanMode`. This replaces Phase 3's approval prompt — the user reviews and approves
   the research plan the same way they would an implementation plan. Rejecting the plan stops
   the run cleanly after Phase 2.
5. On approval, plan mode ends and Phase 4+ proceeds using `{run-dir}/` as before.

**Behaviour when inactive:** ignore this section; Phase 3 uses the plain-text prompt documented
below and `--yes` skips it.

**Detection false-negative:** if the adapter misdetects and the skill tries to write outside the
plan file before approval, the harness blocks the write. That is the current pre-adapter
behaviour — no regression. Pass `--dry-run` to get the same "see before you commit" guarantee
without plan mode.

## Workflow

### Phase 1 — Plan

Dispatch `toolbelt:research-planner` with the user's query. Planner returns:

- **classification** (shape): `straightforward` (1 worker) | `comparison` (2-4) | `complex` (5-10)
- **evidence_locus**: `web` | `web-grounded` | `ops` | `codebase` | `hybrid`, plus the list of
  axes fired. Written into `plan.md` as
  `evidence_locus: ops (axes fired: temporal, metric, named-artefact)` so the user can disagree
  explicitly before Phase 4 dispatches. If the user passed `--locus=…`, the planner honours it
  and records it as `evidence_locus: ops (user override)`.
- **sub-questions**: 3-6 scoped investigation prompts
- **outline skeleton**: H2 headings with one-sentence intents

Write the full planner output to `{run-dir}/plan.md`. **Persist FIRST** — this is the single most
important artifact for surviving context truncation.

See `references/methodology.md` for the shape scaling rules and the six-axis evidence-locus
classifier (Temporal shape, Metric vocabulary, Anomaly/attribution, Resource/tool vocab, Named
artefact, Probe-shaped verb) the planner applies.

### Phase 2 — Codebase reconnaissance

Skip this phase only if the user passed `--no-code` or the query is purely external (e.g. "summarize
the 2025 CVEs in OpenSSL"). Otherwise dispatch `toolbelt:code-reconnaissance` with the user's query.

The recon agent returns a 300-500 token brief in the format specified in
`references/codebase-recon.md`. Write it to `{run-dir}/recon.md`. This brief is passed **verbatim**
inside every downstream worker prompt, so the web research is anchored to your actual versions,
files, and usage sites.

### Phase 3 — User approves outline

Present, in order:

1. The outline from `plan.md`.
2. The `evidence_locus: <value> (axes fired: …)` line verbatim, so the user sees which retrieval
   surface Phase 4 will use.
3. The proposed worker roster (N × `research-worker`, N × `ops-probe`, or one of each for hybrid;
   zero if `locus=codebase`).
4. A one-paragraph summary of the recon brief.

Branch on harness state:

- **Plan mode inactive** — ask the plain-text prompt:
  `"Here's the research plan. Should I proceed, adjust scope, or refocus?"` and wait for
  approval. If `--yes` was passed, skip the prompt and proceed.
- **Plan mode active** — see the Plan-mode adapter section below. Do not use the plain-text
  prompt; the harness will route the approval through `ExitPlanMode`.

**Wait for approval** before dispatching Phase 4 workers. This is the cheap checkpoint; Phase 4
is where tokens burn.

If `--dry-run` was passed, stop here regardless of plan-mode state. Print the plan + recon
summary + locus decision, report the run-dir path, and exit without dispatching Phase 4.

### Phase 4 — Parallel retrieval (web / ops / hybrid / codebase)

The worker dispatch table is keyed on `evidence_locus`:

| `evidence_locus` | Phase 4 dispatch |
| ---------------- | ---------------- |
| `web` | N × `toolbelt:research-worker` (web) |
| `web-grounded` | N × `toolbelt:research-worker` (web), recon brief embedded |
| `codebase` | No Phase 4 dispatch; recon brief feeds Phase 5 directly |
| `ops` | N × `toolbelt:ops-probe`, recon brief embedded |
| `hybrid` | 1 × `toolbelt:ops-probe` + 1 × `toolbelt:research-worker`, recon embedded in both |

Dispatch **in a single assistant message with multiple Agent tool uses** (this is the mechanism
that triggers concurrent dispatch). Each worker prompt uses the same structural template; only
the `<tool_guidance>` and `<source_quality>` blocks differ between web and ops workers.

Template (fill in per sub-question):

```text
<objective>{one sub-question from plan.md}</objective>

<codebase_context>
{the Phase 2 recon brief, verbatim}
</codebase_context>

<output_path>{run-dir}/worker-{N}.md</output_path>

<budget>
Minimum 5 tool calls, target 10, hard cap 15.
Stop at diminishing returns — call complete_task when 3 authoritative sources cover the objective.
(Ops-probe sub-cap: max 3 aws logs start-query calls per probe.)
</budget>
```

Dispatch with `run_in_background: true` so the workers run in parallel and you are notified on
completion. After all workers report complete, verify each `worker-{N}.md` exists and ends with
`Status: COMPLETE` or `Status: BLOCKED`. Relaunch any worker whose output is missing the sigil or
is empty. Surface `Status: BLOCKED` probes (they refused a mutating command) to the user — they
are not a pipeline failure, they are a contract success and a human review signal.

For `locus=codebase` the orchestrator skips this phase entirely and dispatches Phase 5 with only
`recon.md` as input.

Hard caps (from `references/stopping-criteria.md`): **max 20 workers, max 100 total sources, max
500K tokens per run**. If a cap is about to be exceeded, stop and write whatever you have.

### Phase 5 — Synthesis

Dispatch **exactly one** `toolbelt:research-synthesizer`. Pass: the paths to all `worker-*.md`
files, the path to `recon.md`, the path to `plan.md`, and the final report path. The synthesizer
prompt must include the narrative-enforcement block from `references/report-structure.md` verbatim
and instruct the agent to prefill its output with `# Executive Summary\n\n`.

The synthesizer writes to `{report}`. It returns the absolute path plus a 3-sentence summary.

**Do not** dispatch parallel section-writers. Cognition's critique and LangChain's Open Deep
Research post-mortem both found this produces disjointed reports. One agent, one pass, one voice.

### Phase 6 — Citation attribution

Dispatch `toolbelt:citation-agent` with the report path. It:

1. Reads the synthesized report.
2. Reads all `worker-*.md` files to build a source index.
3. Matches every factual claim (numbers, dates, product names, specific assertions) to a source.
4. Inserts numeric markers `[N]` inline, in order of first reference.
5. Appends a flat `## Sources` list at the end of the report.
6. Flags unattributable claims in a tool output — these are candidates for hallucination.

The citation-agent **only edits** the report — it does not rewrite or restructure.

### Phase 7 — Validate & surface

Run the two validation scripts. `${CLAUDE_SKILL_DIR}` expands to this skill's directory:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/validate_report.py" "{report}"
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_citations.py" "{report}"
```

`validate_report.py` checks: structure, word count (3000+), no plan-mode sigils (`TODO`, `Next
steps`, `I will`), citation discipline, no excessive bulleting. `verify_citations.py` checks URL
liveness and DOI resolution for every entry in `## Sources`.

If either script fails, dispatch a **targeted expansion** pass to the synthesizer with the specific
failures — do not regenerate the whole report. For citation failures, dispatch the citation-agent
again with the dead URLs flagged for replacement or removal.

When both scripts pass, print to the user:

```text
Report: {absolute report path}
{3-sentence plain-prose summary of the key finding}
```

**Do not** paste the report body into chat. It is on disk.

## Iron rules

1. Orchestrator reads **paths and summaries** from subagents — never raw file contents from workers.
2. `plan.md` and `recon.md` are persisted **before** any web token is spent. Truncation must be
   survivable — if your context is compacted, you can re-read these to resume.
3. **Single-agent synthesis.** Parallel at retrieval; serial at writing. No exceptions.
4. **Write to file, not chat.** The final report is a file. Only the path + summary reaches the user.
5. **User approves the outline** before Phase 4. Phase 1-3 are cheap; Phase 4+ burn tokens.
6. Hard caps: 20 workers, 100 sources, 500K tokens, 15 tool calls per worker.
7. **Prefer fewer, more capable subagents** over many narrow ones. Anthropic's own system originally
   spawned 50 workers for simple queries — this is the canonical anti-pattern.

## References

Load these on demand — they are not loaded automatically into context:

- [references/methodology.md](references/methodology.md) — OODA loop, scaling rules, source-quality
  heuristics, the Anthropic canon
- [references/codebase-recon.md](references/codebase-recon.md) — reconnaissance brief format, glob
  patterns, LSP-vs-Grep decision
- [references/report-structure.md](references/report-structure.md) — narrative-enforcement block
  (copy verbatim into synthesizer prompt), report structure, anti-bullet directive
- [references/stopping-criteria.md](references/stopping-criteria.md) — budgets, diminishing returns,
  hard caps, the 15× token ratio

Template: [templates/report-template.md](templates/report-template.md) — structural scaffold the
synthesizer fills in.

Scripts (invoked in Phase 7):

- `scripts/validate_report.py` — structural and discipline validation
- `scripts/verify_citations.py` — URL liveness and DOI resolution

## Quick reference

```text
straightforward (lookup)  → 1 worker,  3-10 tool calls
comparison (2-4 options)  → 2-4 workers, 10-15 tool calls each
complex (multi-faceted)   → 5-10 workers, hard cap 20
```

```text
Phase 1: plan          →  plan.md  (shape + evidence_locus + axes fired)
Phase 2: recon         →  recon.md            (skip if --no-code)
Phase 3: user approves outline (ExitPlanMode in plan mode; plain-text otherwise)
Phase 4: N workers in parallel →  worker-1.md … worker-N.md
         dispatch = research-worker / ops-probe / hybrid / (skipped for codebase)
Phase 5: synthesize    →  {date}-{slug}-report.md  (single agent, Opus)
Phase 6: attribute citations (edit in place)
Phase 7: validate & surface (path + 3-sentence summary only)
```

## Common failures and their countermeasures

| Failure                                 | Countermeasure                                       |
| --------------------------------------- | ---------------------------------------------------- |
| Orchestrator context bloats with data   | Subagents write files; orchestrator holds paths only |
| Output becomes a plan, not a report     | Prefill `# Executive Summary`; validate for sigils   |
| Parallel section writers disagree       | Single-agent synthesis (Phase 5 is serial)           |
| SEO content farms cited as primary      | Source-quality heuristics in worker prompt           |
| Hallucinated URLs                       | `verify_citations.py` does post-hoc liveness checks  |
| Duplicate worker investigations         | Planner produces disjoint sub-questions; review plan |
| Over-fanning (50 workers for simple Qs) | Classification gates worker count; hard cap 20       |
| Report < 3000 words                     | `validate_report.py` rejects; expansion pass         |
| Web workers return noise for ops query  | Evidence-locus classifier routes to `ops-probe`      |
| Plan mode blocks orchestrator writes    | Plan-mode adapter gates Phase 3 via `ExitPlanMode`   |

## Resumability

If context is compacted mid-run, resume by reading `{run-dir}/plan.md` and `{run-dir}/recon.md`,
listing `worker-*.md` files to see which completed (`Status: COMPLETE` on last line), and picking up
from the first incomplete phase. The filesystem is the source of truth.
