---
name: repo-audit
description: >
  Conduct a full audit of an uploaded code repository (provided as a zip archive) and produce a
  structured Markdown report of findings — ready to feed into Claude Code to create GitHub issues.
  Use this skill whenever the user uploads or references a zip file of a repository and asks for
  an audit, code review, gap analysis, or any request to find errors, incomplete work, or
  undocumented design decisions. Also trigger when the user asks to "check the repo", "review the
  codebase", "find issues in the project", or similar. The output is a findings document formatted
  so each finding maps directly to a GitHub issue.
---

# Repo Audit

Conduct a comprehensive audit of a repository provided as a zip archive. The output is a
structured Markdown report where every finding includes the fields needed to create a GitHub issue.

## Step 1: Unpack and Orient

Unzip the uploaded archive and map the repository structure: note top-level directories, key
entry points, configuration files, and documentation locations.

```bash
unzip <uploaded-file>.zip -d /tmp/repo-audit-workspace
```

Do not start auditing yet. First read the documentation.

## Step 2: Read the Documentation

Before evaluating any code, read all available documentation to understand the project's intent,
architecture, and design decisions. Prioritise in this order:

1. README (any variant)
2. Docs folder (any .md, .rst, .txt files)
3. Inline comments in entry point files
4. Configuration files (package.json, Cargo.toml, pyproject.toml, Makefile, etc.)

Derive from this reading:
- The project's stated purpose
- The target architecture or reference design (if any)
- Any known intentional deviations from a reference, and whether they are documented

This context is your audit baseline. Every finding must be evaluated against it.

## Step 3: Audit the Codebase

Systematically examine the repository across these dimensions. Do not limit yourself to them, but
cover all of them:

- **Correctness**: bugs, logic errors, broken or missing functionality
- **Completeness**: unfinished implementations, TODOs, stubs, placeholder code, dead code paths
- **Design deviations**: departures from a reference design or spec are acceptable if explicitly
  documented with a rationale — flag any deviation that lacks this justification
- **Code quality**: unclear naming, missing or inadequate comments, inconsistent style,
  copy-paste patterns
- **Configuration and structure**: missing files, incorrect or unpinned dependencies,
  misconfigured tooling, absent CI/CD, missing .gitignore or license
- **Documentation gaps**: missing, outdated, contradictory, or misleading documentation

## Step 4: Produce the Findings Report

Write a single Markdown file. Structure it as follows:

### Document Header

```markdown
# Repo Audit: <Project Name>

## Summary

**Project purpose (inferred):** <one or two sentences>
**Audit date:** <date>
**Total findings:** Critical: X | Major: X | Minor: X

---
```

### Findings

Group findings by severity: Critical first, then Major, then Minor. Within each group, order
findings by category. Use this template for every finding:

```markdown
## Finding: <Short descriptive title>

**Severity:** Critical | Major | Minor
**Category:** Correctness | Completeness | Design Deviation | Code Quality | Configuration | Documentation

### Description
A clear, factual description of the problem. No filler. Reference specific behaviour or observed
state where possible.

### Location
`path/to/file.ext` — line X (or line range X–Y)

### Suggested Fix
A concrete, actionable recommendation. If a code change is needed, include a short illustrative
snippet where useful.

---

### GitHub Issue Fields

- **Title:** <Concise issue title, suitable as a GitHub issue title>
- **Body:** <Full issue body combining description and suggested fix, ready to post as-is>
- **Labels:** <Comma-separated suggested labels, e.g. `bug`, `documentation`, `enhancement`, `refactor`>
```

If no findings exist for a severity level, omit that section entirely. If the project is clean,
produce the summary section and a short paragraph stating what was checked and that no issues
were found.

## Step 5: Save and Present

Save the output as `<project-name>-audit.md` in `/mnt/user-data/outputs/` and present it to the
user using `present_files`.
