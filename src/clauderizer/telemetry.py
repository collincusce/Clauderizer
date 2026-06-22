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
