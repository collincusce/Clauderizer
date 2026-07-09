# Clauderizer hook setup for amp

For Tier-1 automatic status injection, wire this command to amp's session hook (.amp/plugins/*.ts) on these events: session.start, agent.start.

Command: `uvx --from clauderizer clauderizer-hook`

The hook prints the `[Clauderizer]` digest, which amp injects into context. Without it you still have the floor (Tier 4) and /cz-status (Tier 3).
