# glnds-cc-marketplace

Personal plugin marketplace for Claude Code (and claude.ai / Cowork, which load the skills).

## Setup

Register the marketplace once, then install what you need:

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
claude plugin install research@glnds-cc-marketplace
```

Or declare it in `~/.claude/settings.json`; Claude Code clones the marketplace and installs the
enabled plugins in the background on first start:

```json
{
  "extraKnownMarketplaces": {
    "glnds-cc-marketplace": {
      "source": { "source": "github", "repo": "glnds/glnds-cc-marketplace" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "research@glnds-cc-marketplace": true }
}
```

On claude.ai, add it under **Customize > Plugins > Add marketplace** and turn on **Sync
automatically**; the skills then also reach chat, Cowork and Claude Code as `<name>@synced`.

## Plugins

<!-- rumdl-disable MD013 -->
| Plugin | Install key | Description |
| --- | --- | --- |
| [research](./plugins/research/) | `research@glnds-cc-marketplace` | Multi-agent deep research: long-form reports grounded in the codebase, the web and live ops evidence. |
| [audit](./plugins/audit/) | `audit@glnds-cc-marketplace` | Read-only repository audit: severity-ranked findings report for a local checkout. |
| [plan-review](./plugins/plan-review/) | `plan-review@glnds-cc-marketplace` | Adversarial, diagnosis-only review of implementation plans before autonomous execution. |
| [gh-tools](./plugins/gh-tools/) | `gh-tools@glnds-cc-marketplace` | GitHub workflow skills: create well-defined issues and fix PR review feedback. |
| [ty-lsp](./plugins/ty-lsp/) | `ty-lsp@glnds-cc-marketplace` | Python language server (ty) for type checking and code intelligence. |
| [chat](./plugins/chat/) | `chat@glnds-cc-marketplace` | Skills for claude.ai chat and Cowork: Obsidian notes, sparring, text polish, verbalized sampling, zip repo audits. |
| [deploy](./plugins/deploy/) | `deploy@glnds-cc-marketplace` | Ship and verify: commit, push, watch CI and CodePipeline, check the live resources, report evidence. |
<!-- rumdl-enable MD013 -->

## Development

```text
mise run setup                                   # install pinned tools + git hooks
claude --plugin-dir plugins                      # load every plugin from this checkout
mise run check                                   # validate manifests + lint
```

A `--plugin-dir` copy replaces the installed copy of the same name for that session; run
`/reload-plugins` after edits.

### Release

1. Bump `version` in the plugin's `.claude-plugin/plugin.json` (installed copies update only when
   it changes) and add a `CHANGELOG.md` entry.
2. Commit, then tag: `claude plugin tag plugins/<name>` (creates `<name>--v<version>`).

### Layout

```text
.claude-plugin/marketplace.json
plugins/<name>/
├── .claude-plugin/plugin.json
├── skills/<skill>/SKILL.md
├── agents/*.md            # optional
├── .lsp.json              # optional
└── README.md
```

Skills are namespaced by plugin (`/<plugin>:<skill>`), so skill names don't repeat the plugin
name.
