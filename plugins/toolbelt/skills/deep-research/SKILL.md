---
name: deep-research
description: Use when the user asks for research, an audit, a migration analysis, a library comparison, a CVE impact assessment, a technology evaluation, or any question that requires both local codebase context AND current web sources. Produces a long-form narrative report (3000-8000 words) written to disk. NOT for quick lookups — this spends tokens deliberately. Triggers on phrases like "research X", "audit Y", "how does recent X affect us", "compare A vs B", "investigate".
argument-hint: [research topic or question]
allowed-tools: Agent, Bash, Read, Write, Glob, Grep, WebSearch, WebFetch
---

# deep-research

Orchestrator that produces a long-form narrative research report grounded in this codebase AND the
current web. Implements Anthropic's orchestrator-worker pattern with a codebase-reconnaissance phase
prepended so the report names your actual files, versions, and usage sites — not generic summaries.

Topic: `$ARGUMENTS`

## Core contract

- **Narrative prose, not bullets.** Target 3000-8000 words in flowing paragraphs. Written to disk.
- **Grounded in THIS codebase.** Phase 2 recon brief is passed verbatim to every web worker.
- **Parallel retrieval, serial synthesis.** 3-5 workers fan out; one agent writes the final report.
- **Citations are post-hoc.** Synthesizer writes clean prose; citation-agent attributes claims after.
- **Orchestrator never holds raw content.** Subagents write to files; orchestrator reads paths.

## Architecture

This skill runs as the main session and dispatches 5 subagents via the Agent tool:

| Phase | Subagent                        | Model   | Parallelism      |
| ----- | ------------------------------- | ------- | ---------------- |
| 1     | `toolbelt:research-planner`     | inherit | 1                |
| 2     | `toolbelt:code-reconnaissance`  | haiku   | 1                |
| 4     | `toolbelt:research-worker`      | sonnet  | **N in parallel**|
| 5     | `toolbelt:research-synthesizer` | opus    | 1 (serial)       |
| 6     | `toolbelt:citation-agent`       | haiku   | 1                |

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

## Workflow

### Phase 1 — Plan

Dispatch `toolbelt:research-planner` with the user's query. Planner returns:

- **classification**: `straightforward` (1 worker) | `comparison` (2-4 workers) | `complex` (5-10)
- **sub-questions**: 3-6 scoped investigation prompts
- **outline skeleton**: H2 headings with one-sentence intents

Write the full planner output to `{run-dir}/plan.md`. **Persist FIRST** — this is the single most
important artifact for surviving context truncation.

See `references/methodology.md` for the scaling rules the planner applies.

### Phase 2 — Codebase reconnaissance

Skip this phase only if the user passed `--no-code` or the query is purely external (e.g. "summarize
the 2025 CVEs in OpenSSL"). Otherwise dispatch `toolbelt:code-reconnaissance` with the user's query.

The recon agent returns a 300-500 token brief in the format specified in
`references/codebase-recon.md`. Write it to `{run-dir}/recon.md`. This brief is passed **verbatim**
inside every downstream worker prompt, so the web research is anchored to your actual versions,
files, and usage sites.

### Phase 3 — User approves outline

Present the outline from `plan.md` plus a one-paragraph summary of the recon brief to the user. Ask:

> "Here's the research plan. Should I proceed, adjust scope, or refocus?"

**Wait for approval** before dispatching web workers. This is the cheap checkpoint; Phase 4 is where
tokens burn.

### Phase 4 — Parallel web research

Dispatch N `toolbelt:research-worker` subagents **in a single assistant message with multiple Agent
tool uses** (this is the mechanism that triggers concurrent dispatch). Each worker prompt contains:

```text
<objective>{one sub-question from plan.md}</objective>

<codebase_context>
{the Phase 2 recon brief, verbatim}
</codebase_context>

<output_path>{run-dir}/worker-{N}.md</output_path>

<budget>
Minimum 5 tool calls, target 10, hard cap 15.
Stop at diminishing returns — call complete_task when 3 authoritative sources cover the objective.
</budget>
```

Dispatch with `run_in_background: true` so the workers run in parallel and you are notified on
completion. After all workers report complete, verify each `worker-{N}.md` exists and ends with
`Status: COMPLETE`. Relaunch any worker whose output is missing the sigil or is empty.

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
Phase 1: plan          →  plan.md
Phase 2: recon         →  recon.md            (skip if --no-code)
Phase 3: user approves outline
Phase 4: N workers in parallel →  worker-1.md … worker-N.md
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

## Resumability

If context is compacted mid-run, resume by reading `{run-dir}/plan.md` and `{run-dir}/recon.md`,
listing `worker-*.md` files to see which completed (`Status: COMPLETE` on last line), and picking up
from the first incomplete phase. The filesystem is the source of truth.
