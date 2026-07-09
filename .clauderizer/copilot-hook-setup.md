# Clauderizer hook setup for copilot

For Tier-1 automatic status injection, wire this command to copilot's session hook (.github/hooks/*.json) on these events: SessionStart, UserPromptSubmit.

Command: `uvx --from clauderizer clauderizer-hook`

The hook prints the `[Clauderizer]` digest, which copilot injects into context. Without it you still have the floor (Tier 4) and /cz-status (Tier 3).
