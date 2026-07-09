# Clauderizer hook setup for cline

For Tier-1 automatic status injection, wire this command to cline's session hook (.clinerules/hooks/ (POSIX only)) on these events: TaskStart, UserPromptSubmit.

Command: `uvx --from clauderizer clauderizer-hook`

The hook prints the `[Clauderizer]` digest, which cline injects into context. Without it you still have the floor (Tier 4) and /cz-status (Tier 3).
