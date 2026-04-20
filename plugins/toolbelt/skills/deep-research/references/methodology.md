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

## Evidence-locus classifier

Shape alone (straightforward / comparison / complex) decides worker **count**. It does not decide
where the evidence lives. A "compare Lambda duration of 2026-04-11 with 2026-04-19" query is
shape=`comparison` but its evidence lives entirely in CloudWatch and git — dispatching web workers
returns generic "Lambda cost optimization" noise. The planner emits a second axis, `evidence_locus`,
that routes Phase 4 to the right retrieval surface.

Score the query against these six axes. **If ≥ 2 axes fire → `ops`. If exactly 1 fires and the
topic is otherwise generic → `hybrid`. Zero axes → `web` or `web-grounded` as before. A sole
external-topic override forces `web`; a sole codebase-scope override forces `codebase`.**

**Axis 1 — Temporal shape.** Two dates (ISO, `Apr 11`, `11 April`), a date range, relative time
(`yesterday`, `last week`, `Q1`, `during the outage`), a narrow window (`14:00–16:00`), or two
release tags / deploy markers.

**Axis 2 — Metric vocabulary.** `duration`, `latency`, `p50/p95/p99`, `throughput`, `error rate`,
`errors`, `invocations`, `throttles`, `cold starts`, `cost`, `spend`, `bill`, `CPU`, `memory`,
`iops`, `connections`, `queue depth`, `backlog`, `lag`, `saturation`, `availability`, `uptime`,
`success rate`.

**Axis 3 — Anomaly / attribution.** `spike`, `jumped`, `dropped`, `climbed`, `regressed`,
`slower`, `faster`, `higher`, `lower`, `plummeted`, `flatlined`, `degraded`, `outage`,
`incident`, `anomaly`, `off-baseline`, `explained by`, `caused by`, `correlated with`,
`why did`, `what changed`.

**Axis 4 — Resource / tool vocab.** AWS (`Lambda`, `RDS`, `DynamoDB`, `SQS`, `S3`, `API Gateway`,
`CloudFront`, `EventBridge`, `Step Functions`, `ECS`, `EKS`, named CloudWatch alarms); GCP
(`Cloud Run`, `Pub/Sub`, `BigQuery`, `Cloud SQL`); Azure (`Functions`, `Cosmos`, `App Service`);
observability (`Datadog`, `Grafana`, `Prometheus`, `Sentry`, `Honeycomb`, `Splunk`, `ELK`,
`New Relic`); k8s (`pod`, `deployment`, `HPA`, `kubectl`, `OOMKilled`); DB (`slow query`,
`deadlock`, `lock contention`, `replica lag`, `connection pool`, `WAL`); queue (`DLQ`,
`visibility timeout`, `redrive`).

**Axis 5 — Named artefact.** A specific function / table / queue / dashboard / alarm / pipeline
name that looks like it maps to infra (`attracr-essentia-orchestrator`, `orders-api`,
`checkout-dead-letter`, `grafana.internal/d/…`); stack or environment names (`prod`,
`staging-eu`); deploy / release IDs (`v2.47.0`, commit SHA).

**Axis 6 — Probe-shaped verb.** `trace`, `dive`, `attribute`, `localise`, `isolate`, `bisect`,
`correlate`, `aggregate`, `profile`, `drill into`, `break down by`, `group by`, `stats over`;
diagnostic framings like "find the slowest `{resource}`" or "find the N `{resources}` with most
`{metric}`".

Overrides and tie-breakers:

- **Sole external-topic override** — if the query names a CVE ID, RFC number, library version
  diff, vendor announcement, W3C/IETF draft, `npm`/`PyPI`/`crates.io` package name with a version
  number, locus = `web` regardless of other axes.
- **Sole codebase-scope override** — if the query contains "in our codebase", "in this repo", or
  names a file path / function name without any metric vocabulary, locus = `codebase` (recon
  alone; no Phase 4).
- **User override** — the slash command accepts `--locus=web|web-grounded|ops|codebase|hybrid`
  to force a path when the classifier guesses wrong.
- **Explain the decision** — the planner's `plan.md` must include an `evidence_locus:` line of
  the form `evidence_locus: ops (axes fired: temporal, metric, named-artefact)` so the user can
  disagree explicitly before Phase 4 dispatches.

Locus → retrieval worker mapping:

| `evidence_locus` | Phase 4 retrieval |
| ---------------- | ----------------- |
| `web` | N × `toolbelt:research-worker` (web) |
| `web-grounded` | N × `toolbelt:research-worker` (web) + recon |
| `codebase` | No Phase 4; synthesizer reads `recon.md` alone |
| `ops` | N × `toolbelt:ops-probe` (new) + recon |
| `hybrid` | 1 × `toolbelt:ops-probe` + 1 × `toolbelt:research-worker` + recon |

## Ops-probe OODA loop

The ops-probe subagent reuses the OODA loop skeleton but its moves are different. The four
prioritised moves, in order:

1. `aws cloudwatch get-metric-statistics` / `get-metric-data` across the window named in the
   query, grouped by whatever dimension the query specifies (per-function, per-table, per-API).
   This is the cheapest move that delivers the headline delta.
2. If the delta is large and localised, `aws logs start-query` against the relevant log group
   with a Logs Insights query that bins by hour or by a handler / operation dimension. Logs
   Insights is expensive and slow — cap at 3 per probe.
3. `git log --since=… --until=… -- <paths>` constrained to the files the recon brief flagged, to
   correlate the inflection date with a specific commit.
4. `Read` or `Grep` into the files those commits touched for a 2–3 sentence justification that
   connects metric delta, commit, and code change.

Stopping criteria: same three triggers as research-worker (sufficiency, budget, diminishing
returns) plus a hard-block trigger when a probe would require a mutating command — emit
`Status: BLOCKED` instead of calling the command. See `stopping-criteria.md` for the ops-probe
budget caps.

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

The same structural template is filled in per sub-question for **both** research-worker and
ops-probe. Only the `<tool_guidance>` and `<source_quality>` blocks swap out — the other sections
(objective, codebase_context, output_contract, budget) are identical, and the orchestrator treats
the two worker types interchangeably for Phase 5 synthesis.

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
- Single-CLI-command ops questions — "what was my Lambda duration yesterday" answers from one
  `aws cloudwatch get-metric-statistics` call; use the AWS CLI directly, not a research pipeline.
- Things the user has not asked for explicitly — this burns hundreds of thousands of tokens.

If you are tempted to use this skill for a 30-second question, you are using the wrong tool.
