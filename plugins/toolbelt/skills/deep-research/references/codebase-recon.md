# Codebase reconnaissance

The recon phase produces a 300-500 token brief that is passed **verbatim** inside every web
worker's prompt. Without this brief, the research is generic; with it, the final report names the
actual files, versions, and usage sites in this codebase and is dramatically more specific than
anything Claude.ai's Research feature can produce.

## Brief format (enforced)

```text
Repo: {name} | Language: {primary} | Entry points: {list}
Relevant deps: X@1.2.3, Y@4.5.0, Z@6.7.8 (with exact version pins from manifests)
Usage sites: path/to/file.ts:45, path/to/other.ts:12-30 ({total-count} files total)
Patterns in use: {abstraction name}(), {pattern-description}
Abstractions: {wrapper class / adapter / etc.} in {path}
Tests touching this area: {test-file-glob} ({count} tests)
Constraints noted: {runtime, compatibility, license, etc. from config files}
```

Keep it under 500 tokens. If the repo is huge, the brief summarises — it does not enumerate.

## Discovery sequence (deterministic)

The recon subagent runs this sequence. Each step feeds the next.

### 1. Dependency manifests

```text
Glob **/package.json         (Node)
Glob **/requirements*.txt    (Python)
Glob **/pyproject.toml       (Python, modern)
Glob **/Cargo.toml           (Rust)
Glob **/go.mod               (Go)
Glob **/build.gradle*        (JVM)
Glob **/pom.xml              (Maven)
Glob **/*.csproj             (.NET)
Glob **/composer.json        (PHP)
Glob **/Gemfile              (Ruby)
```

Read each manifest found. Extract the **exact pinned version** of any library mentioned in the
query. Record both direct and transitive pins if the query concerns security (CVEs) where
transitives matter.

### 2. Usage sites

For each library, symbol, or concept in the query, grep for imports and call sites:

```text
Grep -n "import.*{libname}"
Grep -n "require\(['\"].*{libname}"
Grep -n "from {libname}"
Grep -n "use {libname}::"
```

Then for specific symbols mentioned in the query:

```text
Grep -n "\b{symbol}\(" --type {lang}
```

Record up to 20 file:line references. If more than 20 exist, pick the most representative 10 and
note the total count.

### 3. Read representative files

Pick 2-5 usage files (not all 20). Preference:

- Files with the highest usage density (grep count per file).
- Files in `src/` over `test/` (unless the query is about testing).
- Entry points (`main.*`, `index.*`, `app.*`, `handler.*`) over leaves.

Read each in full. Identify the **abstraction pattern** — is the library called directly, or wrapped
behind an adapter/wrapper class? This matters for migration impact assessment.

### 4. Test surface

```text
Glob **/*{concept}*.test.*
Glob **/test_*{concept}*.py
Grep -l "{libname}" test/
```

Count the tests that exercise the concept. Note their location. A migration from a well-tested
abstraction is lower-risk than one from an untested direct-use site.

### 5. Constraints

Read (if present):

- `.nvmrc`, `.python-version`, `.ruby-version` — runtime pins
- `tsconfig.json`, `pyproject.toml[tool.*]` — tooling constraints
- `LICENSE`, `NOTICE` — licence restrictions relevant to dependency swaps
- `.github/workflows/*.yml` — CI-enforced constraints

Record any constraint that would narrow the viable migration path.

## LSP vs Grep

For typed languages (TypeScript, Python with stubs, Go, Rust, Java, C#), **prefer LSP when
available**. `find_references` and `document_symbols` produce accurate symbol-level usage maps that
`Grep` cannot match for polymorphic or re-exported symbols.

The pragmatic rule: at start of recon, check LSP availability with an `lsp_server_status` probe (or
its equivalent MCP tool). If present, use it for symbol queries; fall back to Grep/Glob for string
and configuration searches. Do not attempt to build a full semantic index — the cost rarely pays
back for a one-shot research query.

## Skipping recon

The orchestrator skips Phase 2 only when:

- The user passes `--no-code` explicitly.
- The query is **purely external** ("summarize the 2024 CVE disclosures for OpenSSL"). If there is
  any chance the code being reviewed intersects with the topic, run recon.

When in doubt, run recon. It is cheap (Haiku, bounded tool calls) and the recon brief is always at
worst ignored; at best it grounds the entire report.

## What recon does NOT do

- **Does not fetch web content.** That is the worker's job. Recon is local-only.
- **Does not write code.** Read-only. No Edit, Write, or Bash modification commands.
- **Does not follow every tangent.** The brief is 500 tokens, not a full architecture doc.
- **Does not summarize the whole repo.** Scope is *relevant to the query*, not comprehensive.

## Example brief (filled in)

For a query "Is our AWS SDK v2 usage affected by recent boto3 CVEs":

```text
Repo: aws-radar | Language: Python 3.12 | Entry points: src/interfaces/api/*.py, Lambda handlers
Relevant deps: boto3@1.34.51, botocore@1.34.51, aws-lambda-powertools@2.34.2
Usage sites: src/infrastructure/dynamodb/repository.py:18 (client), :34 (resource),
  src/infrastructure/claude/claude_client.py:12, src/infrastructure/cognito/auth.py:8-22
  (12 files total, 47 call sites)
Patterns in use: boto3.client("dynamodb") direct, boto3.resource() for higher-level,
  no custom wrapper class — direct-use pattern throughout infrastructure layer
Abstractions: DynamoDBRepository wraps client at domain-repository boundary; no adapter for boto3
Tests touching this area: tests/integration/test_dynamodb_repository.py (23 tests),
  tests/unit/infrastructure/test_*.py (9 mocked tests using moto)
Constraints noted: arm64 Lambda (Graviton2), Python 3.12 per pyproject.toml, PAY_PER_REQUEST
  DynamoDB (no capacity-related SDK bugs applicable)
```

Note: 500 tokens, scannable, specific. A worker receiving this can now phrase its web queries as
"boto3 1.34.51 CVEs" and "botocore DynamoDB client known issues 2024" — not generic "boto3 security
issues".
