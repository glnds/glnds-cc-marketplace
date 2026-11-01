# chat

Skills for claude.ai chat and Cowork: Obsidian notes, sparring, text polish, verbalized
sampling, zip repo audits.

These skills need claude.ai connectors (Obsidian, AWS Documentation) or chat uploads, so the
plugin targets claude.ai. Add the marketplace under **Customize > Plugins > Add marketplace**.
The Obsidian skills (`make-note`, `sparring`, `text-enhancer`) only work in the Claude desktop
app on the Mac running Obsidian: the vault is reached through a local MCP server (see
[setup](#obsidian-mcp-setup-claude-desktop-app)). Leave the plugin disabled in Claude Code.

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

- Obsidian MCP: `make-note`, `sparring`, `text-enhancer`
- Optional: AWS Documentation connector (`sparring`, `text-enhancer`)

## Obsidian MCP setup (Claude desktop app)

The skills use the MCP server built into the Obsidian
[Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin (v4+):
`tag_list`, `vault_read`, `vault_write`, `search_simple`, `search_query`. It listens on
`https://127.0.0.1:27124/mcp`. claude.ai custom connectors can't reach localhost, and the desktop
config only runs stdio servers, so a pinned `mcp-remote` bridges stdio to HTTP. The API key stays
in the macOS Keychain via [fnox](https://github.com/jdx/fnox); no config file holds it.

1. Install the tools: `mise use -g github:jdx/fnox npm:mcp-remote@0.1.38`. Keep `mcp-remote` on
   0.1.38, the last release by its original authors; later releases changed maintainer.
2. Store the key (plugin settings, "API Key"):

   ```fish
   fnox provider add -g keychain keychain
   fnox set -g -p keychain OBSIDIAN_API_KEY   # paste at the hidden prompt
   ```

3. Save the plugin's self-signed CA. Node trusts it through `NODE_EXTRA_CA_CERTS`:

   ```fish
   mkdir -p ~/.config/obsidian-local-rest-api
   curl -sk https://127.0.0.1:27124/obsidian-local-rest-api.crt \
     -o ~/.config/obsidian-local-rest-api/ca.crt
   ```

4. Add the server to `~/Library/Application Support/Claude/claude_desktop_config.json` and
   restart the app (replace `/Users/me`; the app doesn't expand `~`):

   ```json
   "mcpServers": {
     "obsidian": {
       "command": "/Users/me/.local/share/mise/shims/fnox",
       "args": ["exec", "--", "/Users/me/.local/share/mise/shims/mcp-remote",
                "https://127.0.0.1:27124/mcp", "--transport", "http-only",
                "--header", "Authorization:Bearer ${OBSIDIAN_API_KEY}"],
       "env": { "NODE_EXTRA_CA_CERTS": "/Users/me/.config/obsidian-local-rest-api/ca.crt" }
     }
   }
   ```

   `fnox exec` puts the key in the bridge's environment; `mcp-remote` fills in
   `${OBSIDIAN_API_KEY}` itself, after logging the header, so the key never hits its logs.

Obsidian must be running. Claude Code can't use this endpoint directly: its TLS stack rejects
the plugin CA's name constraints (`UNSUPPORTED_CONSTRAINT_TYPE`).

## Changelog

See the [marketplace CHANGELOG](../../CHANGELOG.md).
