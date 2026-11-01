---
name: make-note
description: Create well-structured notes in Obsidian with intelligent tag suggestions. Use this skill whenever the user asks to create a note, make a note, save something to Obsidian, capture a thought, or write something to their vault. Also trigger when the user says "note this", "add to my vault", "save this to Obsidian", or anything that implies persisting content to Obsidian. Fetches live vault tags via MCP to suggest relevant ones, then creates the note using the vault's Note Template structure.
license: MIT
metadata:
  version: 4.0
---

# Make Note

Create notes in Obsidian's Resources folder using the vault's Note Template, with intelligent tag suggestions based on live vault tag data.

**Requires**: `mcp-obsidian` MCP server. All operations go through MCP — no CLI or bash needed.

---

## Workflow

### Step 1: Fetch Vault Tags

Call `mcp-obsidian:obsidian_get_tags` to retrieve all tags with occurrence counts.

Filter for tags with **3 or more occurrences** — these represent genuine vault patterns. Analyze the note topic against these tags to identify relevant candidates.

### Step 2: Suggest Tags

Propose 3–5 relevant tags and present them as a numbered list. Wait for confirmation before proceeding:

```
I suggest these tags for your note:

1. ai/code-agent
2. secdevops
3. dpg/strategy

Use these, modify them, or add more?
```

### Step 3: Read the Template

Call `mcp-obsidian:obsidian_batch_get_file_contents` with `filepaths: ["Templates/Note Template.md"]`.

Use the returned structure as the base, replacing placeholders:

| Placeholder | Replace with |
|---|---|
| `{{date}}` | Current date as `DD-MM-YYYY` |
| `{{time}}` | Current time as `HH:MM` |
| `{{title}}` | The note title (also used as the filename) |

### Step 4: Create the Note

Compose the full note content (frontmatter + body) and call `mcp-obsidian:obsidian_put_content`:

```
filepath: "Resources/NOTE_TITLE.md"
content: (full markdown with substituted frontmatter + body)
```

Example frontmatter output:

```yaml
---
tags:
  - tag1
  - tag2
created: 11-03-2026 14:30
---
# [[NOTE_TITLE]]

NOTE_BODY
```

**Body guidelines:**
- Only include `## References` and `## Related Notes` sections if there is actual content for them.
- Never add empty sections or dead wiki-links.

### Step 5: Confirm

Tell the user:
- Note created at `Resources/NOTE_TITLE.md`
- Tags applied
- Template used: `Note Template`

---

## Tag Guidelines

### Format Standards

1. Hierarchical tags use slash notation: `cloud/aws`, `ai/agentic`, `music/modular`
2. YAML array format in frontmatter
3. Lowercase only
4. Hyphens for multi-word segments: `platform-engineering`, `code-agent`

### Tag Selection Strategy

1. Prioritize tags already in the vault with 3+ occurrences
2. Prefer specific hierarchical tags over broad ones (`ai/code-agent` over `ai`)
3. Mix at least one broad category tag with one specific subtag
4. Cap at 3–5 tags total
5. Never invent tags not present in the vault unless the content clearly warrants a new category

### Common High-Frequency Tags (reference only — always verify live via MCP)

**Work:** `secdevops`, `dpg`, `context/dpg`, `coding`, `ai`, `cloud/aws`

**Technical:** `ai/code-agent`, `ai/agentic`, `ai/mcp`, `coding/sdd`, `secdevops/architecture`

**Personal:** `music/modular`, `music/modular/diy`, `learning`, `productivity`, `electronics`

---

## MCP Tool Reference

| Tool | Purpose |
|---|---|
| `obsidian_get_tags` | Get all vault tags with occurrence counts |
| `obsidian_batch_get_file_contents` | Read template or existing notes |
| `obsidian_put_content` | Create or overwrite a note (filepath + content) |
| `obsidian_append_content` | Append content to an existing note |
| `obsidian_patch_content` | Insert/replace content at a heading or frontmatter field |
| `obsidian_list_files_in_dir` | Browse a folder in the vault |

---

## Notes on Template Handling

The MCP has no native "apply template" command. The workaround is:

1. Read `Templates/Note Template.md` via `obsidian_batch_get_file_contents`
2. Substitute `{{date}}`, `{{time}}`, and `{{title}}` manually
3. Write the result via `obsidian_put_content`

This produces an identical result to Obsidian's native template insertion.
