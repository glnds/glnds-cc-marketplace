# Stopping criteria

Multi-agent research systems fail in two directions: stopping too early (shallow reports) and
stopping too late (burning hundreds of thousands of tokens for marginal gain). This file encodes the
budgets and stopping rules at three levels.

## Per-worker stopping criteria

A worker stops its OODA loop when **any** of these fires:

1. **Sufficiency**: 3 authoritative primary or secondary sources cover the objective. This is the
   target — do not stop short of 3, do not burn budget past 3 unless contradictions remain unresolved.
2. **Budget exhaustion**: 15 tool calls executed (hard cap). 10 is the target. 5 is the minimum —
   no worker should return having made fewer than 5 calls unless the sub-question was trivially
   answered by the first.
3. **Diminishing returns**: Two consecutive fetches produced nothing new — no new facts, no new
   sources, no new angles. The well is dry.
4. **Dead-end recognition**: The objective is unanswerable with the tools available (e.g., requires
   paywalled content, requires real-time data not exposed, requires judgment the worker cannot
   apply). The worker writes a brief "unable to resolve" note explaining why, then calls complete.

The worker **must** call `complete_task` when any of these fires. Continuing past a stop-condition
is a prompt-compliance failure.

## Per-wave stopping criteria (orchestrator)

After Phase 4 workers report complete, the orchestrator decides whether to dispatch a second wave
or proceed to Phase 5. Proceed to Phase 5 when **all** of:

- Every outline section has at least one worker's findings covering it.
- No worker flagged their objective as "unable to resolve" (if any did, consider a targeted
  re-dispatch with a rephrased objective).
- No clear contradiction between workers requires a tie-breaker investigation.
- The cumulative source count is at least `3 × (number of H2 sections in outline)`.

Dispatch a second wave (1-3 additional workers maximum) when:

- A critical sub-question was under-covered and is load-bearing for the conclusion.
- A contradiction between two workers needs a third independent investigation to resolve.
- The validation script in Phase 7 flagged a coverage gap.

**Do not** dispatch a second wave to pad length. If the findings are thin but complete, the report
is shorter. Padding reads as filler and degrades trust.

## Global stopping criteria (run-level)

Hard caps that terminate the run regardless of completion:

| Resource                 | Cap      | Action on breach                                |
| ------------------------ | -------- | ----------------------------------------------- |
| Total workers dispatched | 20       | No new workers; proceed to synthesis            |
| Total sources cited      | 100      | Dedupe; proceed                                 |
| Total tokens consumed    | 500,000  | Halt; write partial report; flag to user        |
| Wall-clock time          | user-set | Halt; write partial report                      |

If the 500K token cap would be breached, the orchestrator **halts the run**, writes the synthesis
with whatever is gathered, and surfaces a warning to the user: *"This run terminated at the token
budget cap. The report is based on {N} workers with {M} sources. Deeper investigation of {topic} was
truncated."*

## The 15× ratio as a budget sanity-check

A rule of thumb from Anthropic's internal telemetry: deep-research runs consume **roughly 15× the
tokens of a normal chat conversation** (4× from longer outputs, 4× from parallel coordination
overhead). For a moderately complex query, expect:

- 50K-150K tokens per worker (context + fetches + thinking + output)
- 5 workers × 100K = 500K tokens at the Phase 4 high end
- 30K-80K tokens for synthesis (reading all worker files, writing report)
- 20K-40K tokens for citation-agent

Total expected: **200K-700K tokens** for a standard complex run. If you are spending less than 100K,
you are probably short-cutting and should expect a shallow report. If you are spending more than
700K, you are probably over-fanning and should reduce worker count on the next run.

## The Anthropic-canonical "80% of variance" fact

Anthropic's internal eval found that **80% of the performance variance across deep-research runs
was explained by token usage alone**. More tokens → better reports, with diminishing returns past
the ~500K mark. This is a reason to not under-budget, but also a reason to respect the cap — past
500K, you are burning dollars for marginal quality.

## When to halt mid-phase

The orchestrator should halt and ask the user **only** if:

- The user pressed a cost-relevant stop signal.
- The query, on reflection, does not actually require deep research (e.g., the first recon turned
  up an unambiguous answer in a single source).
- An explicit safety concern surfaced (e.g., the research is drifting into dual-use territory the
  user did not authorize).

Otherwise, the orchestrator runs the workflow to completion. Interrupting mid-run to "check in" is
exactly the kind of noise the user ran deep-research to avoid.

## Over-fanning: the canonical anti-pattern

Anthropic's early multi-agent system **spawned 50 subagents for simple queries** before scaling
rules were added. The worker count is gated by the planner's classification:

- `straightforward` → **1 worker**, not 3.
- `comparison` → **2-4 workers**, not 8.
- `complex` → **5-10 workers**, hard cap 20.

If the orchestrator is tempted to dispatch 8 workers for "compare A and B", the planner's
classification was wrong. Re-run the planner with explicit instruction to classify as `comparison`
and pick 3-4 workers maximum.

**Prefer fewer, more capable workers over many narrow ones.** This is Anthropic's own verbatim
guidance and it is correct. One 15-tool-call worker investigating a theme thoroughly produces better
material than three 5-tool-call workers scratching the surface of sub-themes.
