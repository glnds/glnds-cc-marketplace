# AGENTS.md

Personal Claude Code plugin marketplace. Catalog: `.claude-plugin/marketplace.json`; one plugin
per capability under `plugins/<name>/`.

## Bump `version` or nobody gets the change

**An update only arrives when you bump `version` in the plugin's `.claude-plugin/plugin.json`.**
Installed copies stay on their cached version until that string changes, however many commits
you push. Every change to a plugin's files ships with, in the same commit:

1. A `version` bump in `plugins/<name>/.claude-plugin/plugin.json` (semver: fix = patch, new
   skill or behaviour = minor, rename or removal = major). Never set `version` in
   `marketplace.json` as well.
2. A `CHANGELOG.md` entry under the new version.
3. After committing: `claude plugin tag plugins/<name>` (creates `<name>--v<version>`), then
   `git push --follow-tags`.

## Rules

- Skills are namespaced by plugin (`/<plugin>:<skill>`): don't repeat the plugin name in skill
  names.
- A plugin's `name` is its install key (`<name>@glnds-cc-marketplace`). Renaming or removing one
  breaks `enabledPlugins` in `~/source/glnds/claude-config/generic_settings.json`; update it in
  the same change.
- `chat` is for claude.ai (needs connectors); keep Claude Code-only components out of it.
- Plugins can't ship settings, permissions or instructions (`CLAUDE.md`); those live in
  claude-config.

## Develop and check

```bash
claude --plugin-dir plugins   # load the checkout for one session; /reload-plugins after edits
mise run check                # validate manifests (--strict) + rumdl + ruff, same as CI
```
