# Clauderizer MCP setup for codex

codex's MCP config lives at `.codex/config.toml` (TOML config -> guide-only (O-04)). Clauderizer does not edit it automatically; register the server yourself with the portable command:

```
uvx --from clauderizer[mcp] clauderizer-mcp
```

Add a `clauderizer` MCP server entry pointing at that command. Once registered you have the cz_* tools; the AGENTS.md floor already tells the agent to call `cz_status` first.
