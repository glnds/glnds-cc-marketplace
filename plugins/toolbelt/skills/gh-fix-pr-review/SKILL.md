---
name: gh-fix-pr-review
description: Use when the user asks to fix PR review feedback, address Claude Code Action review comments, resolve unresolved review threads, handle inline review suggestions, or work through review issues tagged CRITICAL/HIGH/MEDIUM/LOW on the current PR. Covers both GraphQL review threads and REST PR issue comments, picks the highest severity by default, implements and verifies fixes, then replies on the review.
argument-hint: [issue_number] [--all] [--skip-tests] [--inline] [--comments] [--resolve] [--dry-run] [--pr <number>]
allowed-tools: Bash(gh:*) Bash(git:*) Bash(make:*) Read Write Edit
---

# gh-fix-pr-review

## Overview

Address review issues raised by Claude Code Action (and compatible review bots) on a GitHub pull
request. Reviews arrive via two channels — **inline review threads** (GraphQL `reviewThreads`) and
**PR issue comments** (REST `/issues/{pr}/comments`). This skill inspects both, selects the highest
severity unaddressed issue by default, implements the fix, verifies tests, commits, pushes, and
replies on the review.

User input is passed as `$ARGUMENTS`.

**Iron rules:**

- NEVER `git push` without explicit user confirmation of the diff and commit message.
- NEVER post a review reply or resolve a thread without explicit user confirmation.
- NEVER commit broken code — if tests fail and cannot be fixed cleanly, revert and report.
- NEVER run on `main` / `master`.
- ALWAYS check both sources before reporting "no issues" unless scoped by `--inline` / `--comments`.
- ALWAYS filter review comments by bot author, not by prose alone.
- ALWAYS check if a recommendation is already implemented before editing.
- ALWAYS honour the project's own test command (`make test`, scripts in `package.json`, etc.).

## Arguments

| Argument | Effect |
| --- | --- |
| `issue_number` | Fix a specific issue number. Omit to pick the highest severity. |
| `--all` | Fix every actionable issue in severity order. One commit per fix. |
| `--skip-tests` | Skip test verification. Use sparingly. |
| `--inline` | Inspect only inline review threads. |
| `--comments` | Inspect only PR issue comments. |
| `--resolve` | Resolve the inline thread after fixing (requires confirmation). |
| `--dry-run` | List actionable issues and planned fixes. Make no changes. |
| `--pr <number>` | Target a different PR instead of the current branch's PR. |

### Parsing `$ARGUMENTS`

1. Tokenise on whitespace (standard shell quoting).
2. Flags may appear in any order.
3. The first non-flag token that parses as an integer is `issue_number`.
4. `--pr` consumes the next token as its value.
5. `--inline` and `--comments` are mutually exclusive — reject combinations with
   `Error: --inline and --comments cannot be combined`.

Severity order: `CRITICAL > HIGH > MEDIUM > LOW`. Unmarked issues default to `MEDIUM`.

## Output Behaviour

- Do NOT stream intermediate status while gathering data.
- Only report after all configured sources have been checked and merged.
- An empty result from one source is normal — check all configured sources before concluding.
- If nothing actionable is found, report `No unresolved review issues found on this PR` and stop.

## Step 1: Context Detection

```bash
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "Error: cannot run from main/master. Checkout a feature branch first."
  exit 1
fi

# Use --pr override if provided, otherwise the current branch's PR.
NUMBER="${PR_OVERRIDE:-$(gh pr view --json number -q .number)}"
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
gh pr view "$NUMBER" --json number,headRefName,url,state,isDraft
```

**Stop and inform the user if:**

- No PR exists for the current branch and no `--pr` was passed.
- The PR is `MERGED` or `CLOSED`.

## Step 2: Collect Review Feedback

Query both sources unless a filter flag restricts scope. Identify the **review bot login** once:
typically `github-actions[bot]`, `claude[bot]`, or `claude-code[bot]`. Use this in both filters to
avoid mistaking human comments for bot reviews.

### 2a. Inline Review Threads (skip if `--comments`)

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 10) {
            nodes {
              databaseId
              body
              path
              line
              outdated
              createdAt
              author { login }
              url
            }
          }
        }
      }
    }
  }
}' -F owner="$OWNER" -F repo="$REPO" -F number="$NUMBER"
```

Keep threads where:

- `isResolved: false` AND `isOutdated: false`
- At least one comment authored by the review bot login

> **Pagination caveat:** `first: 100` is the GraphQL cap. If the PR has more than 100 threads, warn
> the user; paginate with `after: $cursor` only if needed.

### 2b. PR Issue Comments (skip if `--inline`)

```bash
gh api repos/$OWNER/$REPO/issues/$NUMBER/comments --paginate
```

Treat a comment as a review when BOTH hold:

1. `author.login` matches the review bot.
2. The body contains one of: `## Code Review`, `Code Review -`, a severity marker
   (`CRITICAL|HIGH|MEDIUM|LOW`), a structured marker (`**Problem:**`, `**Recommendation:**`,
   `**Location:**`), or unchecked checklist items (`- [ ]`).

Select the most recent matching comment as the source of truth.

### 2c. Merge and Prioritise

1. Collect issues from every queried source.
2. Inline: each unresolved, non-outdated thread = one issue.
3. PR comment: parse issues from structured blocks (`### 🔍 **Potential Issues**`, numbered lists)
   or checklist entries.
4. Default severity to `MEDIUM` when unmarked.
5. Sort by severity, then by creation time (oldest first within a tier).
6. Select the target from `$ARGUMENTS` or the top of the sorted list.

## Step 3: Parse the Target Issue

Extract, regardless of source:

- Title / short description
- Severity
- File path(s) and line range(s)
- Problem statement
- Recommendation
- Source metadata (thread id, comment url)

**Inline thread** — path/line from thread metadata; severity from the comment body.

**PR comment issue** — expect either a structured block:

```markdown
#### N. **Issue Title (SEVERITY)**
**Location:** `file.js:line-range`

**Problem:** ...

**Recommendation:** ...
```

…or a checklist entry: `- [ ] Issue description (file.js:line)`.

## Step 4: Check If Already Fixed

```bash
git log --oneline -20
git diff origin/main -- <file_path>
```

Read the file at the cited location and compare against the recommendation.

Three outcomes:

- **Not yet applied** → proceed to Step 5.
- **Applied AND review reply already posted** → skip and continue (or stop).
- **Applied BUT no review reply** → skip to Step 8 (reply-only mode). Confirm with the user, then
  post the reply referencing the commit that actually landed the fix.

> **Outdated-location sanity:** if the cited `file:line` no longer matches the referenced code
> (e.g., file moved, content diverged), warn the user and ask whether to skip or locate the
> equivalent site manually. Inline threads marked `isOutdated: true` are already filtered out.

## Step 5: Implement the Fix

If `--dry-run`, list the planned change(s) and stop — no edits.

Otherwise:

1. Read the relevant file(s).
2. Apply the recommendation with minimal, focused changes.
3. Stay in scope — no drive-by refactors, no unrelated cleanup.

Common patterns: idempotency guards for duplicate listeners, missing cleanup functions, input
sanitisation for security findings, matching test updates when behaviour changes.

## Step 6: Verify the Fix

Skip only when `--skip-tests` is passed (warn the user this bypasses safety).

Detect the test command in this order:

1. `Makefile` with a `test` target → `make test`
2. `package.json` `scripts.test` → `npm test` (or `pnpm` / `yarn` if lockfile indicates)
3. `pyproject.toml` / `pytest.ini` → `pytest` (prefer `uv run pytest` if `uv.lock` exists)
4. `go.mod` → `go test ./...`
5. Fallback: ask the user for the project's test command.

**If tests fail:**

1. Attempt a minimal fix for the failure.
2. If it cannot be fixed cleanly, revert with `git checkout -- <files>` and report:
   `Fix causes test failures, manual intervention needed`.
3. Never commit broken code.

## Step 7: Commit and Push

Show the diff and the proposed commit message, then **ask the user to confirm** before committing.

```bash
git add -A
git commit -m "fix: <issue title from review>

<brief description of what was fixed>

Addresses review issue #<N> (<SEVERITY>)
Review: <comment_url>"
```

Ask again before `git push`. If the push is rejected:

```bash
git fetch
git status
# If behind, pull with rebase to keep history linear:
git pull --rebase
```

Then retry the push. Never `--force` without explicit consent.

## Step 8: Reply to the Review

**Confirm with the user** before posting.

**Inline thread reply:**

```bash
gh api graphql -f query='
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(
    input: {pullRequestReviewThreadId: $threadId, body: $body}
  ) {
    comment { url }
  }
}' -F threadId="$THREAD_ID" -F body="Fixed in commit <sha>."
```

If `--resolve` is set and the user confirms, follow up with:

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { isResolved }
  }
}' -F threadId="$THREAD_ID"
```

**PR comment reply:**

```bash
gh api repos/$OWNER/$REPO/issues/$NUMBER/comments \
  -f body="Fixed issue #<N> (**<Title>**) in commit <sha>.

**Changes:**
- <bullet points>

Remaining issues: <count>"
```

## Step 9: Continue or Complete

- `--all` and issues remain → return to Step 4 with the next highest severity.
- Otherwise report:

```text
Fixed: Issue #<N> - <Title> (<SEVERITY>)
Source: inline thread | PR comment
Commit: <sha>
Tests: passed | skipped
Thread resolved: yes | no | n/a

Remaining issues:
- #2: <Title> (HIGH) [inline]
- #3: <Title> (MEDIUM) [comment]

Run again to fix next issue, or use --all to fix all.
```

## Notes

- Inline threads carry precise `path:line` info; PR comments usually need parsing.
- `--inline` / `--comments` scope the sweep to one channel; they are mutually exclusive.
- `--dry-run` is read-only — no edits, commits, pushes, or replies.
- Severity ordering is strict: `CRITICAL > HIGH > MEDIUM > LOW`.
- Review formats vary with the Claude Code Action prompt — match on severity and
  `**Problem:**` / `**Recommendation:**` / `**Location:**` markers rather than exact headings.
- For PRs with more than 100 threads, warn about pagination rather than silently truncating.
