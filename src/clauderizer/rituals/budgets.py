"""Reserve-window wind-down budgets — declared, derived, dormant. (D-072, D-070 P2)

A gameplan may declare how many working sessions it prices itself at, and each
phase may declare its own share. The engine then does exactly three things at
READ time: count recorded spend, compare against the declaration, and say —
once the reserve window opens — that the current stint is the priced ending.
Nothing blocks, nothing kills, nothing persists (Fractal's caps translated
into INVARIANT-05's advisory model; the authors themselves call budgets "a
brake, not a wall", and here even the brake is only a sentence).

Declaration grammar (markdown-canonical, INVARIANT-01):

    > Budget: 12 sessions            (GAMEPLAN.md header block — gameplan tier)
    **Budget**: 2 sessions           (inside a "### Phase N" block — phase tier)

Two tiers ONLY in the alpha (binding condition): gameplan-sessions and
phase-sessions. Spend is denominated in DISTINCT RECORDED DATES carrying stint
records for the tier (host-stable; a proc tag is at most a tiebreaker, never
the unit — recorded, never estimated). The stint ledger is written by
cz_preflight, so the procedure's own ritual is the recorder; recording
coverage gates whether any of this means anything (O-01, phase-5 matrix).

WIND_DOWN is DERIVED at read time, never persisted and never a flag: spend is
append-only-monotone and the budget re-reads live from markdown, so the state
is sticky until the human raises the number — which IS the sanctioned retune.
``reserve`` = ceil(RESERVE_FRACTION x budget), the tail priced for the Ending
Protocol. A declared budget with zero recorded stints while work is in flight
reads UNTRACKED, never "0 spent, all remaining" (D-070 epistemics: unknown is
not zero). Undeclared repos produce nothing anywhere — byte-identical digests
(INVARIANT-08). Ships dormant: no template default declares a budget.
"""

from __future__ import annotations

import math
import re

from ..paths import RepoPaths

#: The priced-ending tail. A module constant on purpose (binding condition):
#: no config knob, no flag — retuning happens in markdown by raising the budget.
RESERVE_FRACTION = 0.10

_GP_BUDGET_RE = re.compile(r"^>\s*Budget:\s*(\S+)\s+sessions?\s*$", re.M | re.I)
_PH_BUDGET_RE = re.compile(r"^\*\*Budget\*\*:\s*(\S+)\s+sessions?\s*$", re.M | re.I)


def reserve(budget: int) -> int:
    return max(1, math.ceil(budget * RESERVE_FRACTION))


def _parse_value(raw: str):
    """int > 0, or the string ``"malformed"`` — surfaced, never raised."""
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return "malformed"
    return v if v > 0 else "malformed"


def declarations(paths: RepoPaths, gid: str, phase: str | None) -> dict:
    """``{gameplan: int|'malformed'|None, phase: int|'malformed'|None}`` read
    live from GAMEPLAN.md. Absent declarations are ``None`` (the normal,
    dormant state)."""
    out: dict = {"gameplan": None, "phase": None}
    gp = paths.gameplan_dir(gid) / "GAMEPLAN.md"
    if not gp.exists():
        return out
    try:
        text = gp.read_text(encoding="utf-8")
    except OSError:
        return out
    m = _GP_BUDGET_RE.search(text)
    if m:
        out["gameplan"] = _parse_value(m.group(1))
    if phase is not None:
        blk = re.search(rf"^###\s+Phase\s+{re.escape(str(phase))}\b.*?(?=^###\s|\Z)",
                        text, re.M | re.S)
        if blk:
            pm = _PH_BUDGET_RE.search(blk.group(0))
            if pm:
                out["phase"] = _parse_value(pm.group(1))
    return out


def _spent_dates(paths: RepoPaths, gid: str, phase: str | None) -> int:
    """Distinct recorded dates carrying a stint for the tier. Phase ``None``
    means the gameplan tier (any phase counts)."""
    from .. import telemetry

    dates = set()
    for e in telemetry.read_events(paths.telemetry_file):
        if e.get("kind") != "stint" or e.get("gameplan") != gid:
            continue
        if phase is not None and str(e.get("phase")) != str(phase):
            continue
        d = str(e.get("date") or "")[:10]
        if d:
            dates.add(d)
    return len(dates)


def assess(paths: RepoPaths, gid: str, phase: str | None,
           phase_in_flight: bool = False) -> list[dict]:
    """Per-tier records for every DECLARED budget; ``[]`` when nothing is
    declared (dormant default). States: ok | wind_down | over | untracked |
    malformed."""
    if not gid:
        return []
    decl = declarations(paths, gid, phase)
    out: list[dict] = []
    for tier, budget in (("gameplan", decl["gameplan"]), ("phase", decl["phase"])):
        if budget is None:
            continue
        if budget == "malformed":
            out.append({"tier": tier, "state": "malformed", "budget": None,
                        "spent": None, "reserve": None,
                        "detail": "budget declaration is not a positive integer"})
            continue
        spent = _spent_dates(paths, gid, phase if tier == "phase" else None)
        res = reserve(budget)
        if spent == 0:
            state = "untracked" if phase_in_flight else "ok"
        elif spent > budget:
            state = "over"
        elif spent >= budget - res:
            state = "wind_down"
        else:
            state = "ok"
        out.append({"tier": tier, "state": state, "budget": budget,
                    "spent": spent, "reserve": res,
                    "detail": f"{spent}/{budget} session-date(s), reserve {res}"})
    return out


def describe(rec: dict) -> str:
    """The single advisory wording every surface shares (L-55). Phase-aware
    (binding condition): being IN the final budgeted stint is a different
    sentence from having exceeded the budget, and zero recorded spend is
    UNTRACKED — never a claim of headroom."""
    tier = "this phase" if rec["tier"] == "phase" else "this gameplan"
    if rec["state"] == "malformed":
        return (f"the Budget line for {tier} is not a positive integer — fix "
                f"the declaration in GAMEPLAN.md (advisory; nothing blocks).")
    if rec["state"] == "untracked":
        return (f"{tier} declares a budget of {rec['budget']} session(s) but no "
                f"stint is recorded yet — spend is UNTRACKED, not zero; the "
                f"wind-down cannot arm until cz_preflight records stints "
                f"(recording coverage, O-01).")
    if rec["state"] == "over":
        return (f"recorded spend exceeds budget for {tier} "
                f"({rec['spent']}/{rec['budget']} session-dates) — the reserve "
                f"is consumed. Close honestly (run the Ending Protocol, or "
                f"defer with a reason) or raise the `Budget:` line in markdown "
                f"— the advisory never blocks (INVARIANT-05).")
    if rec["state"] == "wind_down":
        return (f"you are IN the final budgeted stint for {tier} "
                f"({rec['spent']}/{rec['budget']} session-dates; reserve "
                f"{rec['reserve']} priced for the ending) — land the Ending "
                f"Protocol before this session closes, or raise the `Budget:` "
                f"line in markdown. Advisory only; nothing blocks.")
    return f"{tier} budget {rec['spent']}/{rec['budget']} session-dates — on track."
