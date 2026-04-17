# Research methodology

This file is load-on-demand reference material for the `deep-research` skill. It is not loaded
automatically — read it when you need to understand **why** a phase is structured the way it is, or
when adapting the skill to an unusual query shape.

## The OODA loop

Every `research-worker` subagent executes an explicit Observe-Orient-Decide-Act loop, taken from
Anthropic's published `research_subagent.md` prompt:

1. **Observe** — what information is already gathered? What is the objective?
2. **Orient** — what are the possible next tool calls? Which is most likely to close the gap?
3. **Decide** — pick the single next query or fetch. State the hypothesis being tested.
4. **Act** — execute the tool call. Emit interleaved thinking about the result. Return to Observe.

The loop terminates when one of three stopping criteria fires:

- 3 authoritative sources cover the objective (hard-to-beat default).
- Tool-call budget is exhausted (5 minimum, 10 target, 15 hard cap per worker).
- Diminishing returns: two consecutive fetches produced nothing new.

Workers are instructed to **start with short broad queries and progressively narrow**. Anthropic's
team found that agents default to overly specific queries that return zero results. "jwt library
vulnerabilities 2024" beats "CVE-2024-12345 impact on jsonwebtoken v9.0.2 async verify path".

## Scaling rules (planner's classifier)

The planner classifies the query into one of three shapes. This determines worker count.

| Shape             | Signals                                     | Workers | Calls per worker |
| ----------------- | ------------------------------------------- | ------- | ---------------- |
| `straightforward` | Single fact, one authoritative source       | 1       | 3-10             |
| `comparison`      | 2-4 options to weigh, explicit "vs" or "or" | 2-4     | 10-15            |
| `complex`         | Multi-faceted, audit-shaped, temporal       | 5-10    | 10-15            |

**Hard ceiling: 20 workers globally per run, ~100 total sources.** Anthropic's early system spawned
50 workers for simple queries — this is the canonical failure mode. Prefer fewer, more capable
workers over many narrow ones.

**Decomposition is disjoint.** The planner produces sub-questions that do not overlap. A worker
researching "CVEs in library X" and a worker researching "deprecations in library X" will duplicate
work; combine into "security and deprecation state of library X" with one worker.

## Source-quality heuristics

Every worker prompt includes this hierarchy (in priority order):

1. **Primary sources**: official docs, RFCs, CVE databases (NVD, GHSA), vendor security advisories,
   standards bodies (IETF, W3C), canonical repositories, release notes from the maintaining org.
2. **Secondary analysis**: established technical publications (LWN, ACM, IEEE, major tech blogs
   from companies with engineering reputation), peer-reviewed papers, authoritative community
   references (MDN, cppreference).
3. **Tertiary synthesis**: Wikipedia (for dates and basic facts only), well-moderated StackExchange
   answers, maintainer blog posts.
4. **Avoid**: SEO content farms, listicles, aggregator sites that rewrite primary sources,
   undated material, passive-voice sourcing ("it is said", "some reports suggest"), AI-generated
   summaries of other sources.

Workers must **flag source quality in their output**. If the only available source for a claim is
tertiary or lower, mark the claim as "single-source, unverified" so the synthesizer can either
search further or explicitly label it in the report.

## The Anthropic canon (do not deviate without reason)

These decisions are from Anthropic's June 2025 engineering post "How we built our multi-agent
research system" and the open-source `claude-cookbooks/patterns/agents/prompts` directory. They are
battle-tested against BrowseComp-style evaluations. Deviate only with a specific reason.

- **Orchestrator-worker pattern.** Orchestrator plans and dispatches; workers execute independently;
  orchestrator synthesizes. No worker-to-worker communication.
- **Multi-agent research uses ~15× the tokens of a chat interaction.** 4× from longer outputs, 4×
  from parallel overhead. Budget accordingly.
- **Opus-lead + Sonnet-workers outperforms Sonnet-only by ~90% on BrowseComp.** The quality gap is
  concentrated at the synthesis step. Use Opus for Phase 5 if available.
- **Parallelism cuts wall-clock time by up to 90%.** Subagents issue parallel tool calls inside
  their own execution too.
- **Subagents write findings to files, not returns.** Returning verbose content to the orchestrator
  creates a "game of telephone" and bloats orchestrator context. Workers write; orchestrator reads.
- **Citations are a separate agent's job.** The synthesizer produces clean prose. The citation agent
  attaches sources in a post-hoc pass. Doing both at once degrades both.
- **Small changes to the orchestrator prompt cause non-deterministic subagent behavior.** The system
  is emergent and stochastic. Invest in evaluation, not reproduction.

## Worker-prompt structure

Every worker receives the same structural template, filled in per sub-question:

```text
<objective>
{one-sentence sub-question, specific and bounded}
</objective>

<codebase_context>
{the Phase 2 recon brief, verbatim — this is what makes the research grounded}
</codebase_context>

<output_contract>
Write findings to {run-dir}/worker-{N}.md.
Structure: one H2 per sub-finding, 2-3 paragraphs of prose per section.
Every factual claim carries a URL inline.
Last line of file must be exactly: Status: COMPLETE
</output_contract>

<tool_guidance>
- WebSearch for snippets, WebFetch for full pages on promising hits.
- Do NOT cite from search snippets alone — fetch the page first.
- Do NOT use Edit/Agent/other subagent-spawning tools.
</tool_guidance>

<source_quality>
Primary > secondary > tertiary. Flag SEO farms, passive-voice sourcing, undated material.
</source_quality>

<budget>
Minimum 5 tool calls, target 10, hard cap 15.
Stop at 3 authoritative sources covering the objective.
Stop when two consecutive fetches produce nothing new.
</budget>
```

## The 15× ratio as a budget mental model

A normal chat turn costs ~1K-5K tokens. A single-agent research run costs ~4× that (~20K). A
multi-agent research run costs ~4× that (~80K) from parallelism overhead plus coordination. Plan for
a 5-worker complex run to cost 300K-500K tokens end-to-end. If you are spending less, you are
probably short-cutting. If you are spending more, you are probably over-fanning.

## When NOT to use deep-research

The skill is designed for token-intensive, long-form, grounded research. It is wrong for:

- Quick factual lookups — use `WebSearch` directly.
- "What does this code do?" — use `Explore` or ask plainly.
- Pure planning tasks — use the `Plan` subagent or superpowers' brainstorming.
- Things the user has not asked for explicitly — this burns hundreds of thousands of tokens.

If you are tempted to use this skill for a 30-second question, you are using the wrong tool.
