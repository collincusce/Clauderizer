"""Append-only, deterministic telemetry of memory surfacing + phase outcomes.

This is the empirical signal the engine has never persisted (Phase 0 of the
empirical-self-improvement-loop gameplan): which lessons/invariants a handoff
SURFACED for a phase, and whether that phase then PASSED its exit criteria.
One compact JSON object per line in ``.clauderizer/telemetry.jsonl``.

Joining the two kinds over time is what makes per-lesson *utility* (Phase 1) and
the *curator* (Phase 2) possible — today every proposer recomputes from a
stateless disk read, so nothing remembers whether surfacing a lesson correlated
with a passing phase.

Constitution:
  * append-only (INVARIANT-03) — every write is a new line; prior lines untouched;
  * deterministic & stdlib-only (D-018) — no ML, no third-party deps; the only
    non-determinism is the date, which is injectable (``today=``) for tests;
  * written ONLY from blessed, already-write-locked ops (cz_write_handoff,
    cz_transition_phase) — never from a hook handler (INVARIANT-06);
  * never auto-acted-on — cz_corpus_health READS and SURFACES; the agent decides
    (INVARIANT-05).

Because both callers already hold the H-05 write lock, the append here needs no
lock of its own.
"""

from __future__ import annotations

import json
import re
from datetime import date as _date
from pathlib import Path

# Token-set Jaccard at/above which two lessons are flagged a near-duplicate. High
# (precision over recall): the curator (Phase 2) would rather miss a loose pair
# than propose merging two lessons that only share boilerplate. Tunable later.
_REDUNDANCY_THRESHOLD = 0.6


def _today(today: str | None) -> str:
    return today or _date.today().isoformat()


def _append(telemetry_file: Path, record: dict) -> None:
    telemetry_file.parent.mkdir(parents=True, exist_ok=True)
    # One compact, key-sorted JSON object per line — append-only (INVARIANT-03),
    # never a rewrite. sort_keys makes a given record's bytes deterministic so
    # round-trip tests can assert equality.
    line = json.dumps(record, sort_keys=True, ensure_ascii=False)
    with open(telemetry_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def record_surfaced(telemetry_file: Path, *, gameplan: str, phase: str,
                    lessons, invariants, gameplan_lessons=None,
                    today: str | None = None) -> dict:
    """Log which project lessons / invariants a handoff surfaced for a phase."""
    rec = {
        "kind": "surfaced",
        "date": _today(today),
        "gameplan": gameplan,
        "phase": str(phase),
        "lessons": sorted({str(x) for x in (lessons or [])}),
        "invariants": sorted({str(x) for x in (invariants or [])}),
        "gameplan_lessons": sorted({str(x) for x in (gameplan_lessons or [])}),
    }
    _append(telemetry_file, rec)
    return rec


def record_outcome(telemetry_file: Path, *, gameplan: str, phase: str,
                   status: str, criteria_total: int, criteria_checked: int,
                   today: str | None = None) -> dict:
    """Log a phase outcome: terminal status + exit-criteria checked/total."""
    rec = {
        "kind": "outcome",
        "date": _today(today),
        "gameplan": gameplan,
        "phase": str(phase),
        "status": status,
        "criteria_total": int(criteria_total),
        "criteria_checked": int(criteria_checked),
    }
    _append(telemetry_file, rec)
    return rec


def read_events(telemetry_file: Path) -> list[dict]:
    """All telemetry events in append order; tolerant of partial/garbled lines."""
    if not telemetry_file.exists():
        return []
    out: list[dict] = []
    # utf-8-sig strips a stray BOM; errors="replace" + the per-line try keep one
    # torn write from aborting the whole read (degrade, don't crash — O-03).
    with open(telemetry_file, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _tokens(text: str) -> set:
    # Deterministic lexical tokens (no ML, D-018): alnum runs > 2 chars, lowered.
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _active_project_lessons(paths) -> list[dict]:
    """``{id, text}`` for each ACTIVE ``L-NN`` lesson in docs/LESSONS.md."""
    from .markdown import lesson_state, sections

    doc = paths.doc("LESSONS")
    if not doc.exists():
        return []
    sec = sections.get_section(doc.read_text(encoding="utf-8"), "Lessons") or ""
    num_re = re.compile(r"^\*\*(L-\d+)\.\*\*\s*(.*)$")
    out: list[dict] = []
    for line in sec.splitlines():
        s = line.strip()
        m = num_re.match(s)
        if m and lesson_state.is_active(s):
            out.append({"id": m.group(1), "text": m.group(2)})
    return out


def corpus_health(paths, *, today: str | None = None) -> dict:
    """Deterministic health snapshot over the project-lesson corpus + telemetry.

    All metrics recompute identically from the same LESSONS.md + telemetry.jsonl
    (no ML, no clock beyond the injectable ``today``). Read-only and advisory
    (INVARIANT-05): the baseline Phase 1's scoring and Phase 2's curator build on.
    """
    lessons = _active_project_lessons(paths)
    events = read_events(paths.telemetry_file)
    surfaced = [e for e in events if e.get("kind") == "surfaced"]
    outcomes = [e for e in events if e.get("kind") == "outcome"]

    toks = [(l["id"], _tokens(l["text"])) for l in lessons]
    redundant: list[tuple[str, str]] = []
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            if _jaccard(toks[i][1], toks[j][1]) >= _REDUNDANCY_THRESHOLD:
                redundant.append((toks[i][0], toks[j][0]))

    ever: set = set()
    for e in surfaced:
        ever.update(e.get("lessons") or [])
    never = [l["id"] for l in lessons if l["id"] not in ever]

    passed = sum(1 for e in outcomes if e.get("status") == "complete")
    pass_rate = round(passed / len(outcomes), 4) if outcomes else None

    return {
        "ok": True,
        "date": _today(today),
        "active_project_lessons": len(lessons),
        "redundant_pairs": len(redundant),
        "redundant_examples": [list(p) for p in redundant[:5]],
        "never_surfaced": len(never),
        "never_surfaced_ids": never[:10],
        "surfaced_events": len(surfaced),
        "outcome_events": len(outcomes),
        "pass_rate": pass_rate,
        "telemetry_events": len(events),
        "summary": (
            f"{len(lessons)} active project lessons; {len(redundant)} redundant "
            f"pair(s); {len(never)} never surfaced; {len(events)} telemetry event(s) "
            f"({len(surfaced)} surfaced, {len(outcomes)} outcome"
            + (f", pass_rate {pass_rate}" if pass_rate is not None else "") + ")"
        ),
    }


def _lesson_signal(*, surfaced_count: int, resolved: int, utility) -> str | None:
    """An advisory, judgment-prompting hint (INVARIANT-05) — never a decision.

    Returns the candidate framing for the agent / Phase 2 curator, or None when
    there isn't enough signal to say anything.
    """
    if surfaced_count == 0:
        return "never-surfaced: consider whether it still earns its place"
    if resolved == 0:
        return None  # surfaced, but no resolved phase yet — not enough signal
    if utility is not None and utility <= 0.34:
        return "low-utility: surfaced but rarely preceded a passing phase — review"
    if utility is not None and utility >= 0.8 and resolved >= 2:
        return "high-utility: recurringly preceded passing phases — promotion candidate"
    return None


def lesson_health(paths, *, window: int = 0) -> dict:
    """Per-lesson empirical health joined from telemetry.

    For each active project lesson: ``utility`` = the fraction of its RESOLVED
    surfacings that PASSED (a surfacing is resolved when the (gameplan, phase) it
    was surfaced for has a recorded outcome; passed = status 'complete'),
    ``failure_risk`` = 1 - utility, ``surfaced_count`` / ``resolved_count``, and
    an advisory ``signal``. Deterministic and read-only (INVARIANT-05; no ML,
    D-018): it SURFACES candidates — the agent (and Phase 2's curator) decides.
    ``window`` > 0 keeps only each lesson's most recent N surfacings (recency by
    append order); 0 = all history.
    """
    lessons = _active_project_lessons(paths)
    events = read_events(paths.telemetry_file)
    surfaced = [e for e in events if e.get("kind") == "surfaced"]
    # (gameplan, phase) -> status of its LAST recorded outcome.
    outcome: dict = {}
    for e in events:
        if e.get("kind") == "outcome":
            outcome[(e.get("gameplan"), e.get("phase"))] = e.get("status")

    per: dict = {l["id"]: [] for l in lessons}
    for e in surfaced:
        key = (e.get("gameplan"), e.get("phase"))
        date = e.get("date")
        for lid in e.get("lessons") or []:
            if lid in per:
                per[lid].append((key, date))

    scores = []
    for l in lessons:
        all_hits = per[l["id"]]
        # Recency / time-decay input: the date this lesson was most recently
        # surfaced (None = never). The curator weights stale, never-reinforced
        # lessons toward obsoletion; window scopes utility to recent surfacings.
        last_surfaced = all_hits[-1][1] if all_hits else None
        hits = all_hits[-window:] if (window and len(all_hits) > window) else all_hits
        resolved = [k for (k, _d) in hits if k in outcome]
        passed = sum(1 for k in resolved if outcome[k] == "complete")
        n = len(resolved)
        utility = round(passed / n, 4) if n else None
        failure_risk = round(1 - utility, 4) if utility is not None else None
        scores.append({
            "id": l["id"],
            "surfaced_count": len(hits),
            "resolved_count": n,
            "utility": utility,
            "failure_risk": failure_risk,
            "last_surfaced": last_surfaced,
            "signal": _lesson_signal(surfaced_count=len(hits), resolved=n, utility=utility),
        })
    scores.sort(key=lambda r: r["id"])
    with_signal = sum(1 for r in scores if r["signal"])
    return {
        "ok": True,
        "lessons_scored": len(scores),
        "with_signal": with_signal,
        "scores": scores,
        "summary": (f"scored {len(scores)} active project lessons from "
                    f"{len(surfaced)} surfacing + {len(outcome)} outcome event(s); "
                    f"{with_signal} carry an advisory signal"),
    }


def _active_gameplan_lessons(paths, gid: str) -> list[dict]:
    """``{id, text}`` for each ACTIVE numbered lesson in the gameplan's
    CHAT-HANDOFF-INDEX 'Accumulated Lessons' (gameplan lessons, not L-NN)."""
    from .markdown import lesson_state, sections

    if not gid:
        return []
    idx = paths.gameplan_dir(gid) / "CHAT-HANDOFF-INDEX.md"
    if not idx.exists():
        return []
    sec = sections.get_section(idx.read_text(encoding="utf-8"), "Accumulated Lessons") or ""
    num_re = re.compile(r"^\*\*(\d+)\.\*\*\s*(.*)$")
    out = []
    for line in sec.splitlines():
        s = line.strip()
        m = num_re.match(s)
        if m and lesson_state.is_active(s):
            out.append({"id": m.group(1), "text": m.group(2)})
    return out


def _gameplan_lesson_utility(paths, gid: str) -> dict:
    """Per-gameplan-lesson utility from the surfaced events' gameplan_lessons
    field (the promote-proposal analogue of lesson_health)."""
    events = read_events(paths.telemetry_file)
    outcome = {(e.get("gameplan"), e.get("phase")): e.get("status")
               for e in events if e.get("kind") == "outcome"}
    per: dict = {}
    for e in events:
        if e.get("kind") != "surfaced":
            continue
        key = (e.get("gameplan"), e.get("phase"))
        for lid in e.get("gameplan_lessons") or []:
            per.setdefault(lid, []).append(key)
    out = {}
    for lid, keys in per.items():
        resolved = [k for k in keys if k in outcome]
        passed = sum(1 for k in resolved if outcome[k] == "complete")
        out[lid] = {"resolved": len(resolved),
                    "utility": (round(passed / len(resolved), 4) if resolved else None)}
    return out


def curate_proposals(paths, gid: str = "") -> dict:
    """PROPOSE corpus-maintenance actions from telemetry-derived health.

    Read-only and advisory like cz_mine_failures (INVARIANT-05): the agent
    confirms genuine ones via the named blessed cz_* write; nothing is mutated
    here. Deterministic, no ML (D-018). Four action kinds:
      * consolidate — a lexically redundant project-lesson pair (re-distill: keep
        the higher-utility one, obsolete the other into it);
      * obsolete    — a never-surfaced or consistently low-utility project lesson;
      * flag        — a mediocre-utility lesson to review (no auto-op);
      * promote     — a high-utility GAMEPLAN lesson worth an L-NN in LESSONS.md.
    """
    health = lesson_health(paths)
    scores = {r["id"]: r for r in health["scores"]}
    lessons = _active_project_lessons(paths)
    proposals: list[dict] = []

    # consolidate: lexically redundant project-lesson pairs.
    toks = [(l["id"], _tokens(l["text"])) for l in lessons]
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            jac = _jaccard(toks[i][1], toks[j][1])
            if jac >= _REDUNDANCY_THRESHOLD:
                a, b = toks[i][0], toks[j][0]
                ua = scores.get(a, {}).get("utility") or 0.0
                ub = scores.get(b, {}).get("utility") or 0.0
                keep, drop = (a, b) if ua >= ub else (b, a)
                proposals.append({
                    "action": "consolidate",
                    "lessons": [a, b],
                    "evidence": f"token-set Jaccard {round(jac, 2)} (lexical near-duplicate)",
                    "suggested_op": "cz_obsolete_lesson",
                    "suggested_args": {"number": drop, "reason": f"consolidated into {keep}"},
                    "note": f"capture a synthesis first if wording differs; keep {keep} (>= utility)",
                })

    # obsolete / flag: from per-lesson utility.
    for r in health["scores"]:
        u, n, sc = r["utility"], r["resolved_count"], r["surfaced_count"]
        if sc == 0:
            proposals.append({
                "action": "obsolete", "lessons": [r["id"]],
                "evidence": "never surfaced in any handoff to date",
                "suggested_op": "cz_obsolete_lesson",
                "suggested_args": {"number": r["id"],
                                   "reason": "never surfaced; likely superseded or out of scope"},
            })
        elif n >= 2 and u is not None and u <= 0.2:
            proposals.append({
                "action": "obsolete", "lessons": [r["id"]],
                "evidence": f"utility {u} over {n} resolved surfacing(s)",
                "suggested_op": "cz_obsolete_lesson",
                "suggested_args": {"number": r["id"],
                                   "reason": "consistently low utility: rarely preceded a passing phase"},
            })
        elif n >= 2 and u is not None and u <= 0.5:
            proposals.append({
                "action": "flag", "lessons": [r["id"]],
                "evidence": f"utility {u} over {n} resolved surfacing(s)",
                "suggested_op": None,
                "note": "review: surfaced but the phase often failed — the wording may mislead, "
                        "or it marks a genuinely hard area",
            })

    # promote: high-utility gameplan lessons -> LESSONS.md.
    gl_util = _gameplan_lesson_utility(paths, gid)
    for gl in _active_gameplan_lessons(paths, gid):
        u = gl_util.get(gl["id"], {})
        if u.get("utility") is not None and u["utility"] >= 0.8 and u.get("resolved", 0) >= 2:
            proposals.append({
                "action": "promote", "lessons": [gl["id"]],
                "evidence": f"gameplan-lesson utility {u['utility']} over {u['resolved']} resolved surfacing(s)",
                "suggested_op": "cz_promote_lesson",
                "suggested_args": {"number": gl["id"]},
            })

    by_action: dict = {}
    for p in proposals:
        by_action[p["action"]] = by_action.get(p["action"], 0) + 1
    return {
        "ok": True,
        "proposal_count": len(proposals),
        "by_action": by_action,
        "proposals": proposals,
        "prompt": ("Each item is a PROPOSAL, not a write. Confirm genuine ones via the "
                   "named blessed cz_* op (the engine proposes; you decide — INVARIANT-05). "
                   "consolidate/obsolete/promote keep the append-only audit trail; flag is review-only."),
        "summary": ((f"{len(proposals)} curation proposal(s): "
                     + ", ".join(f"{k} x{v}" for k, v in sorted(by_action.items())))
                    if proposals else "0 curation proposals"),
    }
