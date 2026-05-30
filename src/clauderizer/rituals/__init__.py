"""The rituals — the parts the original procedure asked the AI to do by hand.

- ``status_bundle`` — the cold-start digest (what the SessionStart hook prints).
- ``handoff`` — cumulative, self-contained phase handoff assembly.
- ``preflight`` — the 7-check pre-flight verification, run for real.
- ``ending`` — the end-of-phase orchestration helper.

These are what turn "instructions the AI must remember" into "operations".
"""
