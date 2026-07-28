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

# One canonical tokenizer for ALL lexical-overlap/similarity in the engine
# (D-041): the redundancy metric here tokenizes exactly like the write-time
# near-duplicate advisory (analyze.near_duplicate_lessons) and the abstract
# index (analyze._tokens), so "near-duplicate lesson" has a single definition.
# The prior local fork kept stopwords + 3-char noise and quietly diverged.
from .analyze import _LESSON_DUP_JACCARD, _tokens

# Token-set Jaccard at/above which two lessons are flagged a near-duplicate.
# SINGLE-SOURCED with the write-time advisory (analyze._LESSON_DUP_JACCARD = 0.40):
# corpus_health / curate_proposals and cz_add_lesson now share ONE near-duplicate
# threshold, not two (0.6 here vs 0.40 there was the incoherence the v1.3.0
# integrity audit flagged). Phase-0 measurement (2026-06-28) showed aligning to
# 0.40 yields 0 false positives on the real 30-lesson corpus while removing the
# contradiction — the value is set by data, not taste (O-01).
_REDUNDANCY_THRESHOLD = _LESSON_DUP_JACCARD


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
                   today: str | None = None, reason: str = "") -> dict:
    """Log a phase outcome: terminal status + exit-criteria checked/total.

    Terminal statuses are complete | failed | deferred (D-070 honest terminal
    vocabulary). ``reason`` carries the agent's own words for a deferred stop
    (stored only when non-empty — existing records keep their shape). Note the
    downstream ``summary()`` pass_rate keeps counting ``complete`` as passed,
    which now honestly means GOAL-MET rate: deliberate scope-cuts land as
    deferred instead of being booked complete."""
    rec = {
        "kind": "outcome",
        "date": _today(today),
        "gameplan": gameplan,
        "phase": str(phase),
        "status": status,
        "criteria_total": int(criteria_total),
        "criteria_checked": int(criteria_checked),
    }
    if reason:
        rec["reason"] = reason
    _append(telemetry_file, rec)
    return rec


# One MCP-server process = one working session; the tag lets a reader break a
# same-date tie without ever being the spend unit itself (D-072: spend is
# denominated in DISTINCT RECORDED DATES — a proc tag is an estimate of a
# session and estimates are never counted).
import uuid as _uuid  # noqa: E402  (scoped import keeps the top of file stable)

PROC_TAG = _uuid.uuid4().hex[:8]


def record_stint(telemetry_file: Path, *, gameplan: str, phase: str,
                 today: str | None = None) -> dict:
    """Log one working stint touching (gameplan, phase) — the budget ledger's
    raw material (D-072). Appended best-effort by cz_preflight, so the
    procedure's own mandated ritual is the spend recorder; readers dedupe by
    distinct date at read time (append-only raw, INVARIANT-03)."""
    rec = {
        "kind": "stint",
        "date": _today(today),
        "gameplan": gameplan,
        "phase": str(phase),
        "proc": PROC_TAG,
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


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _active_project_lessons(paths) -> list[dict]:
    """``{id, text, audience}`` for each ACTIVE ``L-NN`` lesson in docs/LESSONS.md.

    The ``L-NN`` line grammar is single-sourced through
    ``abstract_index.parse_lesson_line`` (#5) — no local copy of the regex; the
    audience tag comes from its sibling ``parse_audience`` (D-043)."""
    from .graph.abstract_index import parse_audience, parse_lesson_line
    from .markdown import lesson_state, sections

    doc = paths.doc("LESSONS")
    if not doc.exists():
        return []
    sec = sections.get_section(doc.read_text(encoding="utf-8"), "Lessons") or ""
    out: list[dict] = []
    for line in sec.splitlines():
        s = line.strip()
        parsed = parse_lesson_line(s)
        if parsed and lesson_state.is_active(s):
            eid, title, body = parsed
            out.append({"id": eid, "text": f"{title} {body}".strip(),
                        "audience": parse_audience(s)})
    return out


# --- D-065 parse reconciliation ------------------------------------------------
#
# Per REGISTER, because the honest expectation differs by document shape and a
# flat heading-count check is vacuous here: the readers DEFAULT, so counts match
# while values are wrong. Only HARDENING is an error condition — every finding
# add_finding writes carries a Status line, so a defaulted one means the reader
# failed. DECISIONS legitimately defaults for the founding entries that predate
# the Status line (O-04); INVARIANTS never carry one by design; LESSONS uses the
# ``**L-NN.**`` form and has no ### entries at all.
_RECONCILE: tuple[tuple[str, str, str, bool], ...] = (
    # (doc name, section, label, status_line_expected_on_every_entry)
    ("HARDENING", "Risks", "hardening", True),
    ("DECISIONS", "Decisions", "decisions", False),
    ("INVARIANTS", "Invariants", "invariants", False),
)


def parse_reconciliation(paths) -> dict:
    """Per-register: how many entries had their status PARSED vs DEFAULTED.

    The D-065 detector. A register whose writer always emits a Status line and
    whose reader defaults on every entry is not "all active" — it is a parser
    that matched nothing, which is an error, not a default.
    """
    from . import analyze
    from .markdown import frontmatter, sections

    out: dict = {}
    offenders: list[str] = []
    for doc_name, section, label, strict in _RECONCILE:
        path = paths.docs / f"{doc_name}.md"
        if not path.exists():
            continue
        _fm, body = frontmatter.split(path.read_text(encoding="utf-8"))
        entries = analyze.parse_entries(body, section)
        defaulted = [e["id"] for e in entries
                     if e.get("status_source") != sections.STATUS_PARSED]
        out[label] = {
            "entries": len(entries),
            "status_parsed": len(entries) - len(defaulted),
            "status_defaulted": len(defaulted),
            # Expected-by-design defaults are not a fault; only `strict`
            # registers must be fully parsed.
            "strict": strict,
            "defaulted_ids": defaulted[:10],
        }
        if strict and defaulted:
            offenders.append(
                f"{doc_name}: {len(defaulted)} of {len(entries)} entries have a "
                f"Status line the reader could not parse ({', '.join(defaulted[:5])})"
            )
    out["ok"] = not offenders
    if offenders:
        out["offenders"] = offenders
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
    # The refusal journal's read-only count (O-03/D-069: a journal with a writer
    # and no reader is a dormant evidence store). Zero renders nothing extra.
    refusals = [e for e in read_events(paths.refusals_file)
                if e.get("kind") == "refusal"]

    toks = [(l["id"], _tokens(l["text"]), l.get("audience", "")) for l in lessons]
    redundant: list[tuple[str, str]] = []
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            # D-043: never pair across audiences — a copywriter rule and a coder
            # rule are not consolidation candidates even when they overlap.
            if toks[i][2] != toks[j][2]:
                continue
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
        "refusal_events": len(refusals),
        "parse_reconciliation": parse_reconciliation(paths),
        # The graph's own honesty report: entity-shaped docs it could not index,
        # and duplicate-id shadowings. Both were previously silent, which made a
        # dropped doc indistinguishable from one that simply has no edges and
        # quietly voided D-018's "the graph knows what depends on what".
        "graph_integrity": _graph_integrity(paths),
        "summary": (
            f"{len(lessons)} active project lessons; {len(redundant)} redundant "
            f"pair(s); {len(never)} never surfaced; {len(events)} telemetry event(s) "
            f"({len(surfaced)} surfaced, {len(outcomes)} outcome"
            + (f", pass_rate {pass_rate}" if pass_rate is not None else "") + ")"
            + (f"; {len(refusals)} refused write(s) journaled — cz_mine_failures "
               "reads them" if refusals else "")
            + (f"; PARSE FAULT — {_recon['offenders'][0]}"
               if not (_recon := parse_reconciliation(paths))["ok"] else "")
            + (f"; GRAPH FAULT — {_gi['summary']}"
               if not (_gi := _graph_integrity(paths))["ok"] else "")
        ),
    }


def _graph_integrity(paths) -> dict:
    """``graph.index.build``'s integrity block, plus a one-line summary.

    Best-effort: an unbuildable graph reports ``ok`` with a note rather than
    breaking the health read (INVARIANT-04 spirit)."""
    try:
        from .graph import index

        report = index.build(paths.docs).integrity()
    except Exception as exc:
        return {"ok": True, "unavailable": str(exc),
                "summary": "graph integrity unavailable"}
    parts = []
    if report["dropped"]:
        parts.append(f"{report['dropped']} entity doc(s) not indexed: "
                     + "; ".join(d["path"] for d in report["drops"][:3]))
    if report["collisions"]:
        parts.append(f"{report['collisions']} duplicate id(s): "
                     + "; ".join(c["id"] for c in report["collision_details"][:3]))
    report["summary"] = " | ".join(parts) if parts else (
        f"{report['entities_indexed']} entities indexed, none dropped")
    return report


def _lesson_signal(*, surfaced_count: int, resolved: int, utility,
                   has_telemetry: bool = True) -> str | None:
    """An advisory, judgment-prompting hint (INVARIANT-05) — never a decision.

    Returns the candidate framing for the agent / Phase 2 curator, or None when
    there isn't enough signal to say anything.
    """
    if surfaced_count == 0:
        if not has_telemetry:
            return ("no telemetry in this checkout (0 events) — 'never surfaced' "
                    "here means UNMEASURED, not unused; telemetry.jsonl is "
                    "machine-local and gitignored")
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
            "signal": _lesson_signal(surfaced_count=len(hits), resolved=n,
                                     utility=utility,
                                     has_telemetry=bool(events)),
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

    Merge-base (D-074, executing D-059's tracked unification): every proposal
    carries a stable content-hash ``id`` over its action + participating lesson
    ids + their TEXTS — never the drifting utility figures — and the per-user
    triage ledger filters the pending set, so a judged proposal stays suppressed
    (cz_dismiss_proposal / cz_defer_proposal, unchanged) until a participating
    lesson's text materially changes and it resurfaces under a new id. Filtering
    is display, never authority (D-013): ``all_proposals`` keeps the unfiltered
    list and ``suppressed_count`` is named in the summary, because the gitignored
    ledger makes suppression machine-local.
    """
    from . import proposals as _proposals

    health = lesson_health(paths)
    scores = {r["id"]: r for r in health["scores"]}
    lessons = _active_project_lessons(paths)
    txt = {l["id"]: l["text"] for l in lessons}
    proposals: list[dict] = []

    # consolidate: lexically redundant project-lesson pairs. Same-audience only
    # (D-043) — consolidation across working roles is never proposed.
    toks = [(l["id"], _tokens(l["text"]), l.get("audience", "")) for l in lessons]
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            if toks[i][2] != toks[j][2]:
                continue
            jac = _jaccard(toks[i][1], toks[j][1])
            if jac >= _REDUNDANCY_THRESHOLD:
                a, b = toks[i][0], toks[j][0]
                # D-070 epistemics: an UNMEASURED utility is never coerced to a
                # measured 0.0. Rank only what was measured; when a side (or
                # both) is unmeasured, the note says so instead of faking a
                # ">= utility" comparison. Keep/drop stays deterministic so the
                # suggested op always has a target.
                ua = scores.get(a, {}).get("utility")
                ub = scores.get(b, {}).get("utility")
                if ua is None and ub is None:
                    keep, drop = a, b
                    note = ("capture a synthesis first if wording differs; "
                            "utility unmeasured for both — choose keep/drop by "
                            "content, not score")
                elif ua is None or ub is None:
                    keep, drop = (a, b) if ub is None else (b, a)
                    kept_u = ua if ub is None else ub
                    note = (f"capture a synthesis first if wording differs; "
                            f"keep {keep} (measured utility {kept_u}; "
                            f"{drop} unmeasured)")
                else:
                    keep, drop = (a, b) if ua >= ub else (b, a)
                    note = (f"capture a synthesis first if wording differs; "
                            f"keep {keep} (>= utility)")
                pair = sorted((a, b))
                proposals.append({
                    "action": "consolidate",
                    # The content hash IS the merge-base: texts, not scores.
                    "id": _proposals.proposal_id("curate", "consolidate", *pair,
                                                 *(txt.get(p, "") for p in pair)),
                    "lessons": [a, b],
                    "evidence": f"token-set Jaccard {round(jac, 2)} (lexical near-duplicate)",
                    "suggested_op": "cz_obsolete_lesson",
                    "suggested_args": {"number": drop, "reason": f"consolidated into {keep}"},
                    "note": note,
                })

    # obsolete / flag: from per-lesson utility.
    for r in health["scores"]:
        u, n, sc = r["utility"], r["resolved_count"], r["surfaced_count"]
        # D-063 removed the "never surfaced -> obsolete" arm, and it was never
        # coded until now. It proposed DELETING a lesson from the absence of
        # .clauderizer/telemetry.jsonl — a machine-local, gitignored file — so on
        # any fresh clone, teammate machine or CI runner it proposed obsoleting
        # 100% of the corpus (measured: 25 of 25, including a lesson promoted the
        # day before and three that are the OUTPUTS of the consolidation ritual).
        # Every other arm below already requires n >= 2 resolved surfacings; this
        # one required no evidence at all. corpus_health still reports the
        # never_surfaced COUNT, which is honest and useful — what is gone is
        # treating that count as grounds for deletion (D-065: no output asserts a
        # property from evidence it never read).
        if n >= 2 and u is not None and u <= 0.2:
            proposals.append({
                "action": "obsolete",
                "id": _proposals.proposal_id("curate", "obsolete", r["id"],
                                             txt.get(r["id"], "")),
                "lessons": [r["id"]],
                "evidence": f"utility {u} over {n} resolved surfacing(s)",
                "suggested_op": "cz_obsolete_lesson",
                "suggested_args": {"number": r["id"],
                                   "reason": "consistently low utility: rarely preceded a passing phase"},
            })
        elif n >= 2 and u is not None and u <= 0.5:
            proposals.append({
                "action": "flag",
                "id": _proposals.proposal_id("curate", "flag", r["id"],
                                             txt.get(r["id"], "")),
                "lessons": [r["id"]],
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
                "action": "promote",
                "id": _proposals.proposal_id("curate", "promote", gid, gl["id"],
                                             gl["text"]),
                "lessons": [gl["id"]],
                "evidence": f"gameplan-lesson utility {u['utility']} over {u['resolved']} resolved surfacing(s)",
                "suggested_op": "cz_promote_lesson",
                "suggested_args": {"number": gl["id"]},
            })

    led = _proposals.load_ledger(paths)
    pending = _proposals.filter_pending(proposals, led)
    suppressed = len(proposals) - len(pending)
    by_action: dict = {}
    for p in pending:
        by_action[p["action"]] = by_action.get(p["action"], 0) + 1
    return {
        "ok": True,
        "proposal_count": len(pending),
        "by_action": by_action,
        "proposals": pending,
        # Display, never authority (D-013): the unfiltered set stays readable.
        "all_proposals": proposals,
        "suppressed_count": suppressed,
        "prompt": ("Each item is a PROPOSAL, not a write. Confirm genuine ones via the "
                   "named blessed cz_* op (the engine proposes; you decide — INVARIANT-05). "
                   "consolidate/obsolete/promote keep the append-only audit trail; flag is "
                   "review-only. Dismiss a false positive with cz_dismiss_proposal(id) — it "
                   "stays suppressed until a participating lesson's text materially changes."),
        "summary": ((f"{len(pending)} curation proposal(s): "
                     + ", ".join(f"{k} x{v}" for k, v in sorted(by_action.items())))
                    if pending else "0 curation proposals")
                   + (f" ({suppressed} suppressed by your ledger — machine-local)"
                      if suppressed else ""),
    }


# Many review-flags in one iteration signal a structural problem a single
# maintenance pass cannot fix; at/above this count a loop iteration SUGGESTS
# escalating to a driven gameplan (never auto-creates one — INVARIANT-05).
_SPAWN_FLAG_THRESHOLD = 3


def loop_step(paths, gid: str = "") -> dict:
    """One iteration of a loop gameplan (read-only).

    Returns the convergence metric (corpus_health), the curator's proposals,
    whether the loop has CONVERGED (no actionable consolidate/obsolete/promote
    proposal remains — review flags don't block), and an escape-hatch
    ``spawn_gameplan`` suggestion when it detects structural work too big for a
    maintenance pass. The agent applies the actionable proposals via their blessed
    cz_* writes, then calls loop_step again; the loop ends when ``converged`` is
    True. Deterministic, no ML (D-018), advisory (INVARIANT-05) — never writes,
    never auto-creates.
    """
    health = corpus_health(paths)
    _has_tel = bool(read_events(paths.telemetry_file))
    curated = curate_proposals(paths, gid)
    proposals = curated["proposals"]          # pending only (merge-base, D-074)
    suppressed = curated.get("suppressed_count", 0)
    actionable = [p for p in proposals if p["action"] in ("consolidate", "obsolete", "promote")]
    flags = [p for p in proposals if p["action"] == "flag"]
    spawn = None
    if len(flags) >= _SPAWN_FLAG_THRESHOLD:
        spawn = {
            "suggested_op": "cz_create_gameplan",
            "reason": (f"{len(flags)} lessons flagged for review (a failure-prone area) - "
                       "bigger than a maintenance pass; consider a driven gameplan to fix the root cause"),
            "lessons": sorted(f["lessons"][0] for f in flags),
        }
    converged = not actionable
    return {
        "ok": True,
        "converged": converged,
        # A ledger-suppressed proposal is judged, not gone (D-063/D-065): the
        # convergence a dismissal buys is machine-local, so it is a NAMED state
        # distinct from a clean corpus, and the summary says so.
        "converged_with_suppression": bool(converged and suppressed),
        "metric": {
            "redundant_pairs": health["redundant_pairs"],
            "never_surfaced": health["never_surfaced"],
            "active_project_lessons": health["active_project_lessons"],
        },
        "actionable_proposals": len(actionable),
        "proposals": proposals,
        "all_proposals": curated.get("all_proposals", proposals),
        "suppressed_count": suppressed,
        "spawn_gameplan": spawn,
        "prompt": ("One loop iteration (read-only). Apply the actionable proposals via their "
                   "blessed cz_* ops, then call cz_loop_step again; the loop ends when converged "
                   "is true. spawn_gameplan, when set, suggests escalating to a driven gameplan "
                   "(the agent decides - INVARIANT-05)."),
        "has_telemetry": _has_tel,
        # A guard that trades a false wipe for a false green is not a fix:
        # "converged" with no evidence to act on is a DIFFERENT state from
        # "converged, corpus healthy" (D-063/D-065).
        "summary": ((("loop iteration: CONVERGED (no telemetry in this checkout — "
                      "nothing measured, not nothing to do)" if not _has_tel
                      else "loop iteration: CONVERGED") if not actionable
                     else f"loop iteration: {len(actionable)} actionable proposal(s)")
                    + f"; metric redundant={health['redundant_pairs']} "
                      f"never_surfaced={health['never_surfaced']}"
                    + (f"; {suppressed} suppressed by your ledger "
                       "(converged-with-suppression — machine-local)"
                       if converged and suppressed
                       else (f"; {suppressed} suppressed by your ledger" if suppressed else ""))
                    + (f"; spawn-gameplan suggested ({len(flags)} flags)" if spawn else "")),
    }
