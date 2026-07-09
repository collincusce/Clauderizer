# Clauderizer hook setup for gemini-cli

For Tier-1 automatic status injection, wire this command to gemini-cli's session hook (.gemini/settings.json (hooks)) on these events: SessionStart, BeforeAgent.

Command: `uvx --from clauderizer clauderizer-hook`

The hook prints the `[Clauderizer]` digest, which gemini-cli injects into context. Without it you still have the floor (Tier 4) and /cz-status (Tier 3).
