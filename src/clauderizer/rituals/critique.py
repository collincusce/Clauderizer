"""The self-critique gate (D-019): assemble a reference-free coverage/coherence/
grounding rubric for a target (a phase or the whole gameplan) by composing the
deterministic signals the engine already computes, and surface it for the AGENT
to grade.

Read-only and advisory like the analyze gate (D-016): the engine ASSEMBLES the
gaps it can detect deterministically and prompts; it never scores or blocks
(INVARIANT-05). Reference-free (no gold standard — fitting, since a coherence-
retention system has no gold artifact to diff against) and stdlib-only (no
embeddings). STORM grades drafts with a reference-free rubric over Interest /
Coherence / Relevance / Coverage; adapted to Clauderizer's grain, the dimensions
are Coverage / Coherence / Grounding, each backed by signals that already exist.
"""

from __future__ import annotations

import re

from ..config import Config
from ..markdown import lesson_state, sections
from ..paths import RepoPaths
from . import _tables, status_bundle as sb

# Provenance marker written by mutations.add_lesson (D-017). A lesson without it
# is un-grounded — the Grounding dimension's signal.
_EVIDENCE_RE = re.compile(r"\*\(evidence:", re.IGNORECASE)
_LESSON_NUM_RE = re.compile(r"^\*\*(\d+)\.\*\*\s*(.*)")


def _lessons_without_evidence(index_text: str) -> list[str]:
    """Active accumulated-lesson lines carrying no provenance marker (D-017)."""
    sec = sections.get_section(index_text, "Accumulated Lessons") or ""
    out: list[str] = []
    for line in sec.splitlines():
        s = line.strip()
        if not sb._LESSON_LINE_RE.match(s) or not lesson_state.is_active(s):
            continue
        if _EVIDENCE_RE.search(s):
            continue
        m = _LESSON_NUM_RE.match(s)
        if m:
            body = m.group(2)
            out.append(f"lesson #{m.group(1)} has no evidence: "
                       + body[:60] + ("…" if len(body) > 60 else ""))
    return out


def _resolve_phase(target: str | None, rows: list) -> str | None:
    """Map a target to a phase number (or None for the whole gameplan).

    None / "" / "gameplan"  -> whole gameplan
    "handoff"               -> the current in-progress phase (the one being handed off)
    "<n>"                   -> that phase
    """
    t = (target or "").strip().lower()
    if t in ("", "gameplan"):
        return None
    if t == "handoff":
        cur = next((r for r in rows if r.status == "in_progress"), None)
        return cur.number if cur else None
    return str(target).strip()


def critique(paths: RepoPaths, config: Config, target: str | None = None) -> dict:
    """Assemble the Coverage/Coherence/Grounding rubric for ``target``."""
    gid = config.active_gameplan
    if not gid:
        return {"ok": True, "target": None, "dimensions": [], "gap_count": 0,
                "summary": "no active gameplan to critique",
                "prompt": "Nothing to critique — no active gameplan."}
    gdir = paths.gameplan_dir(gid)
    index_file = gdir / "CHAT-HANDOFF-INDEX.md"
    status_file = gdir / "PHASE-STATUS.md"
    source = index_file if index_file.exists() else status_file
    text = source.read_text(encoding="utf-8") if source.exists() else ""
    index_text = index_file.read_text(encoding="utf-8") if index_file.exists() else ""
    rows = _tables.parse_phase_table(text)

    phase = _resolve_phase(target, rows)
    scope = f"phase {phase}" if phase else f"gameplan {gid}"

    # --- Coverage: open items + exit criteria addressed? ---
    coverage: list[str] = []
    for it in sb.unresolved_open_items(gdir, phase):
        coverage.append(f"open item {it['id']} unresolved: {it['text'][:70]}")
    crit_phases = [phase] if phase else [r.number for r in rows]
    for pn in crit_phases:
        for c in sb.unchecked_exit_criteria(gdir, pn):
            coverage.append(f"phase {pn} exit criterion unchecked: {c['text'][:70]}")
    if not phase:
        incomplete = [r.number for r in rows if r.status != "complete"]
        if incomplete:
            coverage.append(f"phase(s) not complete: {', '.join(incomplete)}")

    # --- Coherence: nothing contradicted, graph reconciled? ---
    coherence = list(sb._drift_warnings(paths, rows))
    pc = sb.pending_cascades(gdir / "_cascade-reports")
    if pc:
        coherence.append(f"{len(pc)} pending cascade report(s): {', '.join(pc)}")

    # --- Grounding: lessons cite their evidence? (D-017) ---
    grounding = _lessons_without_evidence(index_text)

    dims = [
        {"name": "Coverage",
         "question": "Is every open item resolved and every exit criterion met?",
         "gaps": coverage},
        {"name": "Coherence",
         "question": "Does the work contradict nothing recorded, with the graph reconciled?",
         "gaps": coherence},
        {"name": "Grounding",
         "question": "Does each active lesson cite the evidence that produced it?",
         "gaps": grounding},
    ]
    for d in dims:
        d["clean"] = not d["gaps"]
    gap_count = sum(len(d["gaps"]) for d in dims)
    return {
        "ok": True,
        "target": scope,
        "dimensions": dims,
        "gap_count": gap_count,
        "summary": (f"self-critique of {scope}: {gap_count} gap(s) across "
                    f"{len(dims)} dimensions"),
        "prompt": (
            "Reference-free self-critique (STORM's rubric, adapted to Coverage / "
            "Coherence / Grounding). The engine surfaced the gaps it can detect "
            "deterministically per dimension; YOU grade each dimension and decide "
            "whether to close the gaps or accept them with reason. Advisory — it "
            "never blocks (INVARIANT-05); an empty dimension is a pass on that axis."
        ),
    }
