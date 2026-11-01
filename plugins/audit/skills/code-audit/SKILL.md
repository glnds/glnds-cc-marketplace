---
name: code-audit
description: Use when the user asks to audit, review, analyse, assess, or do a "health check" / "posture assessment" / "risk register" on a repository or subtree; asks to "check the repo", "find issues", "find risks", "look for vulnerabilities", "do a security review", "audit dependencies", "review architecture", "check resilience", or "review infrastructure costs"; or refers to SecDevOps, NFRs, OWASP, ASVS, SBOM, or supply chain at repo scope. Produces a deep, READ-ONLY, severity-ranked Markdown audit REPORT (not a plan, not a spec) written to disk as audit-<slug>-<YYYYMMDD>.md, covering six dimensions in priority order: security, resilience, cost efficiency, architecture and coupling, documentation freshness, monitoring gaps. NOT for style tweaks, formatting, single-function reviews, quick one-file reads, refactor proposals, or design documents — use a normal review or planning flow for those.
argument-hint: "[path-or-subtree] [--scope=security|resilience|cost|architecture|docs|monitoring|all]"
allowed-tools: Read, Grep, Glob, Write, Bash(ls:*), Bash(cat:*), Bash(head:*), Bash(tail:*), Bash(wc:*), Bash(find:*), Bash(rg:*), Bash(grep:*), Bash(sort:*), Bash(uniq:*), Bash(awk:*), Bash(sed:*), Bash(diff:*), Bash(comm:*), Bash(jq:*), Bash(yq:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git branch:*), Bash(git ls-files:*), Bash(git blame:*), Bash(git rev-parse:*), Bash(test:*)
model: opus
effort: high
context: fork
agent: general-purpose
disable-model-invocation: true
---

# code-audit

Performs a deep, **read-only** audit of the repository (or a subtree passed as `$ARGUMENTS`) and
writes a severity-ranked Markdown report to the project root as `audit-<slug>-<YYYYMMDD>.md`. The
skill prioritises thoroughness over speed. It never modifies files inside the audited project, never
runs builds, installers, migrations, or network-mutating commands, and never commits or pushes. The
only write operation it performs is creating the report file itself, outside any source directory it
inspects.

Scope: `$ARGUMENTS`

## Operating contract

- **READ-ONLY against the audited project.** No `Edit`, no `Write` inside the source tree, no
  destructive `Bash`. The single permitted write is the final report at `<repo-root>/audit-*.md`.
- **REPORT, not plan or spec.** Describes current state, grades it, recommends fixes. Does not
  propose a refactor roadmap or design doc.
- **Six dimensions in NFR priority order.** Security > resilience > cost efficiency > architecture
  and coupling > documentation freshness > monitoring gaps. When a finding is ambiguous between
  dimensions, classify under the highest-priority one that applies.
- **Reproducibility.** Every finding pins to `path/to/file.ext:L<start>-L<end>` and the report
  header records the commit SHA from `git rev-parse HEAD`.
- **Read before judging.** A ripgrep hit is a lead, not a finding. Every cited finding must come
  from a file the skill actually opened with `Read`.
- **False negatives over false positives.** Crying wolf destroys trust and breaks downstream issue
  automation. Drop a finding if you cannot verify it in context.
- **No tooling fabrication.** If `semgrep`, `trivy`, `gitleaks`, `osv-scanner`, `infracost`, or
  similar are not on `PATH`, fall back to ripgrep heuristics and note the degraded coverage in
  Methodology. Do not install anything.
- **Redact secrets.** If a real secret is found, record location and type only, with the value
  replaced by `[REDACTED]`. Never echo the value into the report.

## Argument handling

`$ARGUMENTS` may contain:

- A path to narrow the audit, e.g. `packages/api`. Default is the whole tree from
  `git rev-parse --show-toplevel`.
- An optional `--scope=` flag (`security`, `resilience`, `cost`, `architecture`, `docs`,
  `monitoring`, `all`). Default is `all`.

If the path resolves outside the current repository, refuse and ask for an in-repo path.

If the repository is very large (>200k LOC or >50k files), narrow scope and record the narrowing in
the report's Engagement Details section.

## Phase 1 — Map the repository

Establish the shape and stack before reading deeply. Determine the repository root, languages
present, ecosystems involved, IaC footprint, and overall size. Inventory entry points (`main`,
`app`, `index`, `handler`, `lambda_function`, HTTP routers), dependency manifests (`package.json`,
`pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle*`, `Gemfile`,
`composer.json`), IaC (`*.tf`, `*.tfvars`, `template*.yaml`, `serverless.yml`, `cdk.json`,
`Pulumi.yaml`, `*.bicep`), containers (`Dockerfile*`, `docker-compose*.yml`), CI
(`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`), and top-level docs (`README*`,
`SECURITY.md`, `CHANGELOG*`, `docs/`, `adr*/`).

Useful commands:

```bash
git rev-parse --show-toplevel
git rev-parse HEAD
git log -1 --format='%cs %s'

rg --files --hidden --no-ignore \
  -g '!.git' -g '!node_modules' -g '!vendor' -g '!dist' -g '!build' | head -200

rg --files \
  -g 'package.json' -g 'pyproject.toml' -g 'requirements*.txt' \
  -g 'go.mod' -g 'Cargo.toml' -g 'pom.xml' -g 'build.gradle*' \
  -g 'Gemfile' -g 'composer.json'

rg --files \
  -g '*.tf' -g 'template*.yaml' -g 'serverless.yml' \
  -g 'cdk.json' -g 'Pulumi.yaml' -g '*.bicep'

rg --files -g 'Dockerfile*' -g 'docker-compose*.yml'

find . -type f \
  \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' \
     -o -name '*.go' -o -name '*.java' -o -name '*.rb' -o -name '*.cs' \) \
  ! -path '*/node_modules/*' ! -path '*/vendor/*' ! -path '*/.git/*' \
  -exec wc -l {} + | tail -1
```

Produce an internal stack summary: primary languages by LOC, frameworks detected, cloud provider(s)
in IaC, runtime targets, approximate service count. Feeds the report's Engagement Details section.

## Phase 2 — Deep read

Read the files that determine risk: every HTTP or message-queue entry point, every authentication
and authorization layer, every database access module, every external HTTP client factory, every IaC
module that provisions data stores or network endpoints or compute, and every CI workflow that
publishes artefacts. Read these end-to-end with `Read`; do not rely on grep excerpts for anything
you plan to cite in a finding.

When reading authentication code, trace one request from entry to data access and back. When reading
IaC, list the resources provisioned and look for obvious defaults (no retention, no lifecycle, no
encryption, no tags). When reading CI, confirm third-party actions are pinned by SHA, that secrets
are injected from the secret store and not from plaintext, and that release artefacts produce an
SBOM and ideally a provenance attestation.

## Phase 3 — Dimensional audit

Run the six dimensional passes in priority order. For each, consult the matching reference for the
full checklist, tools, and grep patterns. Architecture and coupling lives inline because the
heuristics are short.

### 3.1 Security (highest priority)

Aligned to OWASP Top 10:2025 RC and ASVS v5.0.0. Cover access control (including SSRF, folded into
A01 in 2025), cryptographic failures, injection across all sinks, authentication, software supply
chain (A03 in 2025, standalone), logging and alerting failures, and mishandling of exceptional
conditions (A10 in 2025, new). See [references/security-checklist.md](references/security-checklist.md)
for grep patterns and tool invocations.

Preferred tools when available: `gitleaks detect --no-git`, `trivy fs --scanners vuln,secret,misconfig,license`,
`semgrep scan --config p/owasp-top-ten --config p/security-audit`, `osv-scanner scan source -r`,
`bandit` for Python, `gosec` for Go.

### 3.2 Resilience

Every external call must have an explicit timeout. Every retry must be bounded and jittered. Every
resource must be cleaned up. Every error must be either handled or deliberately propagated, never
swallowed. Every cross-service call must carry a correlation or trace identifier. See
[references/resilience-checklist.md](references/resilience-checklist.md) for ecosystem-specific
patterns.

### 3.3 Cost efficiency

IaC waste first — biggest lever at a media company. CloudWatch log groups without
`retention_in_days` default to never-expire. S3 buckets without lifecycle keep every object in
Standard forever including abandoned multipart uploads. ECR without lifecycle grows unbounded.
Lambda over 1024 MB or off `arm64` is frequently over-provisioned. Previous-generation instance
families (`m5`, `c5`, `r5`, `t2`, `t3`) often have a cheaper Graviton equivalent. High-cardinality
Prometheus or Datadog labels (user IDs, request IDs, emails) blow up metric-store cost. Single-stage
Docker builds ship build toolchains into production. See
[references/cost-patterns.md](references/cost-patterns.md).

### 3.4 Architecture and coupling

Red flags are short, so they live here:

- Files over 500 LOC; functions over 50 LOC; cyclomatic complexity over 15.
- Cyclic module graphs.
- Hub-and-spoke `utils` / `common` / `helpers` packages imported everywhere.
- Controllers containing SQL or HTTP-client calls.
- ORM or framework annotations leaking onto domain entities.
- Singletons holding request-scoped state.

```bash
find . -type f \( -name '*.py' -o -name '*.ts' -o -name '*.go' -o -name '*.java' \) \
  ! -path '*/node_modules/*' ! -path '*/vendor/*' -exec wc -l {} + | sort -rn | head -30
rg -n '(from|import)\s+(pg|psycopg2|pymongo|sqlalchemy|boto3)\b' \
  -g '**/controllers/**' -g '**/handlers/**' -g '**/routes/**' -g '**/api/**'
rg -n 'getInstance\(\)|__new__\s*\(cls\)'
```

When `madge`, `dependency-cruiser`, `import-linter`, `radon`, `gocyclo`, or `lizard` are available,
run them in report-only mode and include output under the Architecture section.

### 3.5 Documentation freshness

Detect drift: README commands referencing removed scripts, env vars read in code that are missing
from `.env.example`, OpenAPI routes that diverge from declared routes, absent `SECURITY.md`, absent
or stale ADRs under `docs/adr/` or `adr/`, TODO/FIXME/HACK/XXX density by area, CHANGELOG freshness.
See [references/docs-and-monitoring.md](references/docs-and-monitoring.md).

### 3.6 Monitoring gaps

Treat A09:2025 (Security Logging and Alerting Failures) and SRE alert hygiene as the bar. Every
HTTP handler should emit a metric and a span. Every alert rule must have a `runbook_url`
annotation. Every service exposes distinguishable `/health`, `/ready`, `/live`. Every log line on
the request path carries a correlation or trace identifier. SLOs and error budgets committed as
code. See [references/docs-and-monitoring.md](references/docs-and-monitoring.md).

## Phase 4 — Write the report

Write the report with `Write` to `<repo-root>/audit-<slug>-<YYYYMMDD>.md`, where `<slug>` is the
repository or subtree name in kebab-case and `<YYYYMMDD>` is today's date. Use the structure in
[references/report-template.md](references/report-template.md).

The report is a REPORT, not a plan and not a spec: it describes current state, grades it, and
recommends changes. Keep recommendations short-term (this release) and long-term (next quarter) at
the finding level. Keep systemic recommendations in the closing section. Do not propose a detailed
implementation.

Each finding uses the template in `references/report-template.md`, with an ID
`[C-NN]` / `[H-NN]` / `[M-NN]` / `[L-NN]` / `[I-NN]` numbered sequentially within severity.

**Severity criteria:**

- **Critical** — immediate compromise of confidentiality, integrity, availability, or funds on a
  realistic path.
- **High** — significant compromise on a realistic path.
- **Medium** — material risk under specific conditions.
- **Low** — circumstantial or limited impact.
- **Informational** — hardening, defence in depth, or code quality with no direct security impact.

**Difficulty:** Low (any motivated actor) / Medium (specific position or authenticated access) /
High (unlikely preconditions).

**Effort:** Trivial (<1h) / Small (<1d) / Medium (<1w) / Large (>1w).

The executive summary is one to two pages of prose: engagement context, overall posture verdict in
one sentence, the findings-count heat map by severity and category, the top 3-5 findings as bullets
linking to their IDs, thematic observations, short-term vs long-term recommendation split. Include
a codebase-maturity rubric table rating Access Controls, Cryptography, Configuration, Error
Handling, Observability, Resilience, Dependency Hygiene, Cost Posture, Documentation, and Testing
on a Strong / Satisfactory / Moderate / Weak / Missing scale with a one-line justification each.

Findings suitable for direct GitHub issue creation should follow the title format
`[AUDIT-YYYY-QN][SEV-NN] <imperative description>`. Suggested labels are listed in
`references/report-template.md`.

## Output to the user

After writing, return only:

- A confirmation that the report was written.
- The absolute report path.
- A one-paragraph top-line summary: overall posture verdict + count of Critical and High findings.

Do not paste the report body into chat. It is on disk.

## Quick reference

```text
Phase 1: map        →  internal stack summary
Phase 2: deep read  →  entry points, auth, IaC, CI, data access
Phase 3: dimensions →  security → resilience → cost → architecture → docs → monitoring
Phase 4: write      →  audit-<slug>-<YYYYMMDD>.md at repo root
Output:             →  path + one-paragraph verdict only
```

| Reference                                                     | When to load                  |
| ------------------------------------------------------------- | ----------------------------- |
| [security-checklist.md](references/security-checklist.md)     | Phase 3.1 — secrets, sinks    |
| [resilience-checklist.md](references/resilience-checklist.md) | Phase 3.2 — timeouts, retries |
| [cost-patterns.md](references/cost-patterns.md)               | Phase 3.3 — IaC waste         |
| [docs-and-monitoring.md](references/docs-and-monitoring.md)   | Phase 3.5+3.6 — drift, alerts |
| [report-template.md](references/report-template.md)           | Phase 4 — report skeleton     |

## Hard prohibitions

- No `Edit`, `Write` (except the final report), `MultiEdit`.
- No installers (`npm install`, `pip install`, `go install`, `cargo install`, `brew`, `apt`).
- No builders (`make`, `npm run build`, `go build`, `cargo build`, `sam build`, `docker build`).
- No git write subcommands (`commit`, `push`, `merge`, `rebase`, `reset`, `checkout`, `tag`).
- No network-mutating tools (`curl -X POST/PUT/DELETE`, `wget --post`, `aws ... create/put/delete`).
- No execution of code discovered in the repository.
