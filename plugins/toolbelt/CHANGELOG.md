<!-- markdownlint-disable MD013 MD024 -->
# Changelog

All notable changes to the `toolbelt` plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
