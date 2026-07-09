<!-- clauderizer:start -->
## Clauderizer

This repo uses Clauderizer for durable, cross-session memory (an MCP server exposes it as cz_* tools). **At the start of every session, call `cz_status` first** — it loads the gameplan, phase, baseline, and open items. To begin or continue work, call `cz_next_phase_context` then `cz_preflight`. Never hand-edit tracked docs; use the cz_* tools.
<!-- clauderizer:end -->
