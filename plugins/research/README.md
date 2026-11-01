# research

Multi-agent deep research: long-form reports grounded in the codebase, the web and live ops evidence.

## Installation

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
claude plugin install research@glnds-cc-marketplace
```

## Skills

### `research:deep-research`

Multi-agent orchestrator that produces a long-form narrative research report (3 000–8 000 words)
grounded in the local codebase, the current web, **and** live ops evidence (CloudWatch metrics,
Logs Insights, `git log`). Dispatches six specialised subagents across a seven-phase workflow:
plan → codebase recon → user-approved outline → parallel workers (web / ops-probe / hybrid) →
single-agent synthesis → citation pass → validation. Output is written to
`./research/{date}-{slug}-report.md`.

The planner emits an **evidence-locus** (`web`, `web-grounded`, `ops`, `codebase`, `hybrid`)
alongside the shape classification, so ops-shaped queries route to the read-only `ops-probe`
subagent instead of noisy web workers. The skill is **plan-mode-aware**: when the harness is in
plan mode, `ExitPlanMode` becomes the Phase 3 approval gate instead of fighting it. A
self-disclosure block prints the tool surface before any token-expensive phase.

Not a quick-lookup tool — spends tokens deliberately (~200 K–700 K per run).

**Flags:** `--no-code` (skip codebase reconnaissance),
`--locus=web|web-grounded|ops|codebase|hybrid` (override the classifier),
`--dry-run` (stop after Phase 2), `--yes` (skip the Phase 3 approval gate outside plan mode).

## Agents

Dispatched by `deep-research`; not meant for direct use:

- `research:research-planner`
- `research:code-reconnaissance`
- `research:research-worker`
- `research:ops-probe`
- `research:research-synthesizer`
- `research:citation-agent`

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
