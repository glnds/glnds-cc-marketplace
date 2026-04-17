<!-- markdownlint-disable MD013 -->
# Claude Code Plugins

Personal plugin marketplace for Claude Code.

## Setup

Register this marketplace (one-time):

```text
claude plugin marketplace add glnds/glnds-cc-marketplace
```

## Available plugins

| Plugin | Install command | Description |
| --- | --- | --- |
| toolbelt | `claude plugin install toolbelt@glnds-cc-marketplace` | My collection of day-to-day tools to get the job done. |

## Contributing

Add new plugins under `plugins/<plugin-name>/` following the standard Claude Code plugin structure:

```text
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json
├── skills/
├── README.md
└── LICENSE
```

See `plugins/toolbelt/` for a reference implementation.
