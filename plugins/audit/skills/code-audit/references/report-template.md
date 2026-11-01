# Audit report template

Use this skeleton for `audit-<slug>-<YYYYMMDD>.md`. Fill in everything in `< >` placeholders.

````markdown
# <Project> code audit — <YYYY-MM-DD>

- Repository: <origin URL>
- Commit: <SHA>
- Scope: <paths or "whole repo">
- Auditor: Claude Code `code-audit` skill, model `opus`
- NFR priority order: security > resilience > cost efficiency

## 1. Executive summary

### 1.1 Engagement overview

Two to three sentences: what was audited, which commit, over what period, what was excluded.

### 1.2 Overall posture

One-sentence verdict. For example: "The service is in good shape on resilience and cost, with one
Critical access-control gap and a systemic supply-chain weakness."

### 1.3 Findings by severity and category

| Category             | Critical | High | Medium | Low | Info | Total |
| -------------------- | :------: | :--: | :----: | :-: | :--: | :---: |
| Access Control       |          |      |        |     |      |       |
| Cryptography         |          |      |        |     |      |       |
| Injection            |          |      |        |     |      |       |
| Supply Chain         |          |      |        |     |      |       |
| Resilience           |          |      |        |     |      |       |
| Cost Efficiency      |          |      |        |     |      |       |
| Architecture         |          |      |        |     |      |       |
| Documentation        |          |      |        |     |      |       |
| Monitoring           |          |      |        |     |      |       |
| **Total**            |          |      |        |     |      |       |

### 1.4 Top findings

Three to five bullet links to the most important findings.

### 1.5 Thematic observations

Two to four paragraphs on recurring patterns across the codebase.

### 1.6 Codebase maturity

Rate each on: Strong / Satisfactory / Moderate / Weak / Missing.

| Dimension          | Rating | Justification |
| ------------------ | ------ | ------------- |
| Access Controls    |        |               |
| Cryptography       |        |               |
| Configuration      |        |               |
| Error Handling     |        |               |
| Observability      |        |               |
| Resilience         |        |               |
| Dependency Hygiene |        |               |
| Cost Posture       |        |               |
| Documentation      |        |               |
| Testing            |        |               |

## 2. Engagement details

### 2.1 Scope

Paths included and excluded; languages detected; size in files and LOC.

### 2.2 Methodology

Phases executed; read-only guarantees; tool availability (note any tool that was unavailable and
therefore replaced by heuristics); confidence caveats.

### 2.3 Threat model

Actors considered, assets, trust boundaries. Keep to half a page.

## 3. Summary of findings

| ID   | Title | Category | Severity | Difficulty | Location  |
| ---- | ----- | -------- | -------- | ---------- | --------- |
| C-01 | ...   | ...      | Critical | Low        | path:L12  |

## 4. Detailed findings

### 4.1 Critical

#### [C-01] <imperative title describing the bug>

| Field      | Value                                |
| ---------- | ------------------------------------ |
| Severity   | Critical                             |
| Difficulty | Low / Medium / High                  |
| Category   | <one of the categories from §1.3>    |
| CWE        | CWE-...                              |
| Location   | `path/to/file.ext:L12-L34` @ <SHA>   |
| Status     | Open                                 |

**Description.** Two to five sentences on what the bug is and why it is a bug.

**Evidence.**

```<lang>
// minimal code excerpt with line numbers
```

**Exploit scenario.** One concrete narrative of abuse.

**Impact.** Business and technical consequences.

**Likelihood.** Who can trigger it and under what preconditions.

**Recommendation.**

- Short term: exact code-level fix.
- Long term: systemic improvement such as a linter rule, invariant test, or process change.

**Effort.** Trivial / Small / Medium / Large.

**References.** CWE links, OWASP ASVS IDs, prior CVEs.

### 4.2 High

### 4.3 Medium

### 4.4 Low

### 4.5 Informational

## 5. Recommendations

### 5.1 Short term (this release)

Prose recommendations that aggregate across findings.

### 5.2 Long term (next quarter)

Architectural, process, and tooling changes.

## 6. Appendices

### A. Severity and difficulty criteria

### B. Tools run and their versions

### C. Files excluded from the audit

### D. GitHub issue-ready titles

For each finding intended to become an issue:

`[AUDIT-<YYYY-QN>][SEV-NN] <imperative title>`

Suggested labels: `audit:<YYYY-qn>`, `severity:<level>`, `difficulty:<level>`,
`category:<name>`, `status:open`, `effort:<size>`.
````
