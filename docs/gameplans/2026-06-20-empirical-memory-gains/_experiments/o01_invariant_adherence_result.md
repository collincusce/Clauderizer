# O-01 — invariant-adherence eval result (inconclusive)

Workflow `phase6-invariant-adherence-eval` (8 agents, 4 invariant-violation probes ×
surfaced/control). Asked each agent whether it would implement a naive request that
violates a specific project invariant, with the relevant invariant surfaced (treatment)
or not (control).

## Result

| Arm | Honored (refused/adapted the violation) |
|-----|------|
| surfaced (invariant in context) | **4/4** |
| control (not surfaced) | **4/4** |

delta = 0. Verdict: **no measured adherence difference.**

## Why it is INCONCLUSIVE, not a clean disproof

1. **Control not isolated.** The agents ran with repo + CLAUDE.md access and cited the
   real invariants (INVARIANT-05/03/01/06), `docs/INVARIANTS.md`, `TRUST.md`, even
   `D-025`/`L-07` from the control arm. So the contrast was "surfaced in handoff" vs
   "available in repo but not surfaced" — not "present vs absent."
2. **Primed framing.** The prompt asked "would you refuse if this conflicts with a
   rule?", triggering the exact rule-check the pointer is meant to prompt — masking any
   proactive-reminder value in both arms.
3. **Ceiling.** 4/4 both arms; the probes were caught every time.

## The real signal

Agents honor these invariants from CLAUDE.md / the repo **without** the handoff pointer
— the same redundancy that justified DROPPING the steering doc in Phase 6. The
focused-invariant pointer's adherence benefit is therefore **unproven and plausibly
redundant**, but it is cheap, focused, injects nothing when no invariant is relevant,
and was shipped honestly (Phase 6 claimed a measured *capability* + inherited mechanism,
never a proven adherence gain). It is retained as-is; a definitive answer needs an
**unprimed, isolated** eval (self-contained arms with no repo access, subtler violations,
and a neutral "here is a task, proceed" framing).
