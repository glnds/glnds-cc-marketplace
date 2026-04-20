<!-- markdownlint-disable MD013 MD024 -->
# Changelog

All notable changes to the `toolbelt` plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2026-04-20

### Added

- `deep-research`: evidence-locus classifier — planner now emits a second axis (`web`,
  `web-grounded`, `ops`, `codebase`, `hybrid`) alongside the shape classification, decided by a
  six-axis scoring rule (temporal shape, metric vocab, anomaly/attribution, resource/tool vocab,
  named artefact, probe-shaped verb). Full rules and overrides in
  `references/methodology.md` § Evidence-locus classifier. Phase 4 dispatches the right worker
  type for the locus instead of always fanning out to web workers.
- `deep-research`: new sibling subagent `toolbelt:ops-probe` for `locus=ops` queries. Same
  output contract as `research-worker` (`worker-{N}.md`, trailing `Status: COMPLETE`), different
  tool surface — read-only AWS CLI + `aws logs start-query` + `git log` + `Read`/`Grep`. OODA
  moves prioritised: CloudWatch metrics → Logs Insights (sub-cap 3 per probe) → git correlation
  → code justification. Budget 15 commands hard cap, 10 target, 5 min; max 2 probes per run.
  Read-only contract pasted verbatim into the subagent so it is self-contained (subagents do
  not inherit `~/.claude/CLAUDE.md`). Mutating commands refused with `Status: BLOCKED`.
- `deep-research`: plan-mode adapter — the skill detects a `Plan mode is active` system-reminder
  and uses `ExitPlanMode` as the Phase 3 approval gate instead of fighting the harness. Plan
  file becomes the home of `plan.md`; Phases 1–2 (read-only) run unchanged; approval via
  `ExitPlanMode` gates Phase 4+.
- `deep-research`: self-disclosure blocks — the skill prints its tool access surface before any
  token-expensive phase. Moment 1 (plan mode active) goes into the plan file alongside the
  outline; Moment 2 (plan mode inactive) goes to chat before Phase 1.
- `deep-research`: `--locus=web|web-grounded|ops|codebase|hybrid` flag overrides the classifier
  when the user already knows where the evidence lives.
- `deep-research`: `--dry-run` flag stops after Phase 2 regardless of plan-mode state — same
  "see before you commit" guarantee that plan mode provides, usable outside plan mode.
- `deep-research`: `--yes` flag skips the Phase 3 approval gate when running outside plan mode.

### Changed

- `deep-research`: `scripts/verify_citations.py` tolerates non-URL entries in `## Sources`
  (metric queries, commit SHAs, other ops primary evidence). Non-URL entries are reported as
  "skipped — non-URL primary source" rather than failed. Exit 0 when there are non-URL entries
  only and no URLs to liveness-check.
- `deep-research`: `templates/report-template.md` Sources example now shows a mixed section
  with metric queries, commit SHAs, and URLs to reflect the ops-locus reports the skill can
  now produce.
- `deep-research`: architecture table in `SKILL.md` adds `toolbelt:ops-probe` as a sibling of
  `toolbelt:research-worker`. Common-failures table adds two entries: noisy-web-workers-for-ops
  and plan-mode-blocking-orchestrator-writes.

## [0.7.0] - 2026-04-19

### Added

- `gh-create-issue`: parse "blocked by" hints from the input prompt and create the native GitHub
  dependency via the `addBlockedBy` GraphQL mutation, so the relationship shows up in the sidebar
  and project views, not only in the issue body. Parsing is prompt-only — no new question is
  asked, on the design principle that blockers are the exception, not the rule, and an extra
  prompt would annoy the 90% case that has none. Triggers on phrases like `blocked by 211`,
  `blocked by issue 211`, `blocked by #211`, `blocked by #211 and #219`. Non-triggers documented
  (`we might be blocked later`, `this blocks 211`, `depends on #211`). Links via
  `gh api graphql` after `gh issue create` returns the new number; the `Target issue has already
  been taken` validation error is swallowed as a no-op so re-runs are idempotent. Any other
  mutation failure is surfaced but does not abort the run — the issue is already created. A
  `## Dependencies` section is appended to the issue body so the link is visible in prose too.

## [0.6.0] - 2026-04-19

### Added

- `adversarial-plan-review` skill — destructive, diagnosis-only pre-flight review of an
  implementation plan, designed to sit between Superpowers' `writing-plans` and
  `subagent-driven-development`. Runs as a dispatched subagent in a fresh context with only the
  plan and spec paths as input (context starvation keeps it adversarial, not sympathetic). Applies
  three priority-ordered attack angles — Structural, Operational, Scope — and emits a severity-
  tagged findings table plus a binary verdict (`PASS` / `NEEDS REWORK` / `NEEDS HUMAN`). No
  remediation, no rewrites, findings capped at 20. One-pass-per-session rule enforced at two
  levels (main agent in `SKILL.md`, reviewer in verdict rules) so the skill cannot drift into a
  constructive-reviewer loop. Ships with `review-prompt.md` (verbatim reviewer prompt) and a
  `README.md` containing the ready-to-paste CLAUDE.md routing block.

## [0.5.0] - 2026-04-17

### Changed

- `deep-research`, `gh-create-issue`, `gh-fix-pr-review`: add
  `disable-model-invocation: true` — these skills all have side effects or spend significant
  tokens (200K-700K for research, GitHub mutations for the two `gh-*` skills), so Claude no longer
  auto-loads them. Invoke explicitly via `/deep-research`, `/gh-create-issue`,
  `/gh-fix-pr-review`.
- `gh-create-issue`: add `allowed-tools: Bash(gh:*) Read Write WebFetch` and
  `argument-hint: "[title-or-plan-text]"` — pre-approves the `gh` CLI calls the skill makes and
  improves autocomplete.
- `deep-research`: switch `allowed-tools` to the space-separated form documented in the Claude
  Code Skills reference.

### Added

- `code-audit` skill — read-only deep audit of a repository or subtree producing a severity-ranked
  Markdown report (`audit-<slug>-<YYYYMMDD>.md`) at the repo root. Trail-of-Bits-style findings
  (Severity × Difficulty, short/long-term recommendations, effort estimate). Six dimensions in NFR
  priority order: security (OWASP Top 10:2025 RC, ASVS v5) → resilience → cost efficiency →
  architecture & coupling → documentation freshness → monitoring gaps. Never modifies the audited
  project — the only write is the report. Falls back to ripgrep heuristics when scanners
  (`gitleaks`, `trivy`, `semgrep`, `osv-scanner`, `infracost`, `checkov`) are absent. Five
  on-demand reference files (security/resilience/cost/docs+monitoring checklists, report
  template). `disable-model-invocation: true` — fires only on explicit `/code-audit` invocation.
  Optional flag: `--scope=security|resilience|cost|architecture|docs|monitoring|all`.

## [0.4.0] - 2026-04-17

### Added

- `deep-research` skill — multi-agent orchestrator producing long-form narrative research reports
  (3000-8000 words) grounded in the local codebase and the current web. 7-phase workflow:
  planner → codebase reconnaissance → user-approved outline → parallel web workers (3-5, hard cap
  20) → single-agent synthesis → citation attribution → validation. Output written to
  `./research/{date}-{slug}-report.md` on disk, not chat.
- Five plugin subagents backing the skill: `research-planner`, `code-reconnaissance`,
  `research-worker`, `research-synthesizer`, `citation-agent`.
- Validation scripts: `validate_report.py` (structure, word count, anti-plan-mode discipline),
  `verify_citations.py` (URL liveness + DOI resolution).

## [0.3.0] - 2026-04-17

### Added

- `gh-fix-pr-review` skill — fix Claude Code Action review feedback on the current PR. Inspects
  both inline review threads and PR issue comments, picks the highest severity unaddressed issue
  by default, implements and verifies the fix, then commits and replies on the review.
  Flags: `--all`, `--skip-tests`, `--inline`, `--comments`, `--resolve`, `--dry-run`,
  `--pr <number>`.

## [0.2.0] - 2026-04-17

### Added

- `gh-create-issue` skill — produce well-defined GitHub issues (single, epic, or sub-issues)
  with label discovery and a TDD plan for implementation-ready issues.

## [0.1.0] - 2026-04-17

### Added

- Initial plugin scaffold. No skills yet.
