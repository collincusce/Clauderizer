# Clauderizer hook setup for codex

For Tier-1 automatic status injection, wire this command to codex's session hook (~/.codex/config.toml or .codex/hooks.json) on these events: SessionStart, UserPromptSubmit.

Command: `uvx --from clauderizer clauderizer-hook`

The hook prints the `[Clauderizer]` digest, which codex injects into context. Without it you still have the floor (Tier 4) and /cz-status (Tier 3).
