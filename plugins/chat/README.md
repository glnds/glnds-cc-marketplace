# chat

Skills for claude.ai chat and Cowork: Obsidian notes, sparring, text polish, verbalized
sampling, zip repo audits.

These skills need claude.ai connectors (Obsidian, AWS Documentation) or chat uploads, so the
plugin targets claude.ai. Add the marketplace under **Customize > Plugins > Add marketplace**.
Claude Code can load it too, but leave it disabled there unless you configure an Obsidian MCP
server.

## Skills

### `chat:make-note`

Create Obsidian notes from the vault's Note Template, with tag suggestions from live
vault tags.

### `chat:sparring`

Critical-thinking partner for technical ideas and strategy, grounded in your Obsidian
notes and, for AWS topics, AWS documentation.

### `chat:text-enhancer`

Grammar, clarity and fact-check pass on professional and technical text. Triggers on
"enhance" or "polish".

### `chat:verbalized-sampling`

Generate several answers with probabilities to escape mode collapse and see the
response distribution. Useful for brainstorming and creative tasks.

### `chat:repo-audit`

Audit a repository uploaded as a zip archive and produce a Markdown findings report where each
finding maps to a GitHub issue. In Claude Code, use `audit:code-audit` on the checkout instead.

## Prerequisites

- Obsidian connector (`obsidian_*` tools): `make-note`, `sparring`, `text-enhancer`
- Optional: AWS Documentation connector (`sparring`, `text-enhancer`)

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
