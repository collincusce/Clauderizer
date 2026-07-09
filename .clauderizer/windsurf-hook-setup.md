# Clauderizer hook setup for windsurf

For Tier-1 automatic status injection, wire this command to windsurf's session hook (.windsurf/hooks.json) on these events: pre_user_prompt.

Command: `uvx --from clauderizer clauderizer-hook`

The hook prints the `[Clauderizer]` digest, which windsurf injects into context. Without it you still have the floor (Tier 4) and /cz-status (Tier 3).
