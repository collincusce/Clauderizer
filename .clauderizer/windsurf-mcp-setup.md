# Clauderizer MCP setup for windsurf

windsurf's MCP config lives at `~/.codeium/windsurf/mcp_config.json` (global MCP config -> guide-only (D-031)). Clauderizer does not edit it automatically; register the server yourself with the portable command:

```
uvx --from clauderizer[mcp] clauderizer-mcp
```

Add a `clauderizer` MCP server entry pointing at that command. Once registered you have the cz_* tools; the AGENTS.md floor already tells the agent to call `cz_status` first.
