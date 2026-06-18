"""The shared ops registry — one dispatch surface for MCP and CLI (L-05, D2).

Every ``cz_*`` operation lives here as a plain function whose name, signature,
and docstring ARE the tool contract: the MCP server registers these exact
function objects (so its schemas derive from them), and ``clauderize ops``
executes them from JSON batches. One table, two transports — the surfaces
cannot drift.

Ops resolve the repo from the working directory on every call (stateless,
matching the MCP server's behavior). Write ops serialize on the H-05 write
lock: mutation-backed ops lock inside ``mutations.*``; the ops that write
through other paths (cascade reports, handoff regeneration, the active-
gameplan config flip) take the lock here in their bodies, so MCP and CLI
callers inherit it identically. Read ops never lock (L-03).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import mutations
from .config import Config
from .graph import cascade as cascade_mod
from .graph import index, query
from .locking import write_lock
from .paths import RepoPaths, find_repo_root, resolve
from .profiles import detect
from .rituals import handoff, preflight, status_bundle


def repo_ctx() -> tuple[RepoPaths, Config]:
    """Resolve the clauderized repo from cwd — shared by every op and resource."""
    root = find_repo_root(Path.cwd())
    paths = resolve(root)
    if not paths.config_file.exists():
        raise RuntimeError(
            "not a clauderized repo (no .clauderizer/config.toml). Run `clauderize init`."
        )
    return paths, Config.load(paths.config_file)


def _graph(paths: RepoPaths):
    return index.load_or_rebuild(paths.docs, paths.index_file)


# --- read / context ops ---------------------------------------------------------


def cz_status() -> dict:
    """Current state: active gameplan, phase table, baseline tests, pending cascades, blockers."""
    paths, config = repo_ctx()
    bundle = status_bundle.compute(paths, config)
    # Long-lived servers only: nudge when the engine source on disk is newer
    # than this process (a fresh CLI/ops process never sees True).
    bundle["engine_stale"] = status_bundle.engine_source_newer_than(
        status_bundle.PROCESS_STARTED)
    return bundle


def cz_next_phase_context() -> dict:
    """Assemble everything the next/current phase session needs in one call (read-only: returns the handoff text without writing a file)."""
    paths, config = repo_ctx()
    bundle = status_bundle.compute(paths, config)
    target = bundle.get("current_phase") or bundle.get("next_phase")
    if not target or not config.active_gameplan:
        return {"ok": False, "summary": "no active/next phase", "status": bundle}
    result = handoff.assemble(paths, config, config.active_gameplan, target["number"], write=False)
    result["phase"] = target
    result["status_summary"] = bundle.get("summary")
    result["next_action"] = bundle.get("next_action")
    return result


def cz_graph_query(entity_id: str = "", kind: str = "lookup", transitive: bool = False) -> dict:
    """Query the Project DAG. kind = lookup | dependents | dependencies. Empty id with kind=lookup lists all entities and pin violations."""
    paths, _ = repo_ctx()
    g = _graph(paths)
    if not entity_id and kind == "lookup":
        return {
            "ok": True,
            "entities": [e.to_dict() for e in g.all()],
            "pin_violations": [vars(v) for v in query.pin_violations(g)],
        }
    if kind == "dependents":
        ids = query.transitive_dependents(g, entity_id) if transitive else query.dependents(g, entity_id)
        return {"ok": True, "entity": entity_id, "dependents": ids}
    if kind == "dependencies":
        return {"ok": True, "entity": entity_id, "dependencies": query.dependencies(g, entity_id)}
    ent = g.get(entity_id)
    return {"ok": ent is not None, "entity": ent.to_dict() if ent else None}


def cz_analyze(text: str, k: int = 5) -> dict:
    """Surface the existing decisions/invariants most relevant to `text`, plus the
    one-hop graph neighbors `text` touches but has not connected — for you to judge
    contradiction/supersession AND gaps (the analyze gate, D-016/D-018).

    Judgment-based like cz_cascade and read-only: the engine ASSEMBLES candidates
    (relevant entries by keyword + entity-id overlap; the `adjacent` graph entities
    by one-hop structural adjacency) and prompts; it never decides. Use before
    recording a decision, or to vet a phase/plan against recorded memory. If a
    surfaced entry is contradicted, record a correction or revise; if superseded,
    set `supersedes` on cz_add_decision; if an `adjacent` entity should have been
    accounted for, that is a gap to close before proceeding.
    """
    paths, _ = repo_ctx()
    from . import analyze as _analyze

    res = _analyze.analyze(paths, text, k=k)
    n = len(res["decisions"]) + len(res["invariants"])
    adj = res.get("adjacent") or []
    res["ok"] = True
    res["prompt"] = (
        "Review against the text. (1) CONTRADICTION/SUPERSESSION: does it contradict "
        "any surfaced decision/invariant (record a correction or revise) or supersede "
        "one (set supersedes on cz_add_decision)? (2) GAPS: the `adjacent` entries are "
        "graph-neighbors of what you're touching that nothing here has connected to "
        "this text — decide whether your change should account for them. The engine "
        "surfaces candidates only; you decide."
    )
    res["summary"] = (
        f"surfaced {n} relevant entr{'y' if n == 1 else 'ies'} "
        f"+ {len(adj)} adjacent for review"
    )
    return res


def cz_critique(target: str = "") -> dict:
    """Self-critique gate (D-019): surface a reference-free Coverage/Coherence/
    Grounding rubric for `target` — a phase number, "gameplan" (default), or
    "handoff" (the current in-progress phase) — for YOU to grade.

    Read-only and advisory like cz_analyze: the engine ASSEMBLES the gaps it can
    detect deterministically (unresolved open items, unchecked exit criteria,
    graph drift, pending cascades, lessons lacking provenance) grouped by
    dimension, and prompts; it never scores or blocks (INVARIANT-05). Reference-
    free and stdlib-only. Run it before completing a phase, before trusting a
    handoff, or at gameplan close.
    """
    paths, config = repo_ctx()
    from .rituals import critique as _critique

    return _critique.critique(paths, config, target=target or None)


# --- ritual ops ------------------------------------------------------------------


def cz_preflight() -> dict:
    """Run the pre-flight checks (git state + host test/build commands) for real.

    A green test run with a measured count also refreshes the active
    gameplan's tracked baseline ("Current baseline test count"), so the
    status digest can't go stale on it.
    """
    paths, config = repo_ctx()
    profile = detect.load_for_repo(config.host_profile, paths.profile_lock)
    # No op-level lock: preflight runs the host's test/build commands for
    # minutes — holding the write lock that long would trip stale takeover.
    # Its single tracked write (the baseline refresh) locks at the write site.
    return preflight.run(paths, config, profile).to_dict()


def cz_cascade(entity_id: str, transition: str, dry_run: bool = False) -> dict:
    """Walk the DAG forward from a changed entity and write a cascade report."""
    paths, config = repo_ctx()
    if not config.active_gameplan:
        return {"ok": False, "error": "no active gameplan for the report dir"}
    g = _graph(paths)
    reports_dir = paths.gameplan_dir(config.active_gameplan) / "_cascade-reports"
    if dry_run:
        res = cascade_mod.run(g, entity_id, transition, reports_dir, dry_run=True)
    else:
        # Report writes serialize with every other tracked write (H-05);
        # this path doesn't route through mutations.*, so lock here.
        with write_lock(paths.write_lock_file):
            res = cascade_mod.run(g, entity_id, transition, reports_dir, dry_run=False)
    # The full report is written to disk; don't dump the whole markdown blob
    # back through the tool result (keeps the return shallow + JSON-clean).
    res.pop("report_md", None)
    return res


def cz_resolve_cascade(verdicts: dict[str, str] | None = None,
                       updates_applied: str = "", updates_deferred: str = "",
                       report: str = "", gameplan_id: str = "") -> dict:
    """Record the verdicts for a cascade report's "needs review" dependents.

    After cz_cascade flags dependents, decide each one and record it here —
    verdicts maps entity id -> what was done ("no change needed", "updated
    pin to ^2.0.0", …); updates_applied summarizes the concrete edits.
    report defaults to the most recent pending report. The report stays
    "pending" (blocking the cascade_hygiene preflight check) until every
    placeholder is resolved. This is the blessed write — never hand-edit
    cascade reports.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.resolve_cascade(paths, gameplan_id=gid, report=report,
                                     verdicts=verdicts,
                                     updates_applied=updates_applied,
                                     updates_deferred=updates_deferred)


def cz_write_handoff(phase_n: str, gameplan_id: str = "") -> dict:
    """Assemble the cumulative, self-contained handoff for a phase."""
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    # Handoff regeneration writes the handoff file + lesson roll-up marks;
    # not mutations.*-routed, so serialize here (H-05).
    with write_lock(paths.write_lock_file):
        return handoff.assemble(paths, config, gid, phase_n)


# --- mutation ops ----------------------------------------------------------------


def cz_create_gameplan(name: str, first_phase: str = "Bootstrap") -> dict:
    """Scaffold a new gameplan directory and make it active."""
    paths, config = repo_ctx()
    # The scaffold write locks inside mutations.*; the active-gameplan config
    # flip must sit in the same critical section (reentrant), or two creators
    # could interleave scaffold and flip.
    with write_lock(paths.write_lock_file):
        result = mutations.create_gameplan(paths, name, first_phase=first_phase)
        config.active_gameplan = result["gameplan_id"]
        paths.config_file.write_text(config.to_toml(), encoding="utf-8")
    return result


def cz_add_phase(name: str, goal: str, depends_on_phases: list[str] | None = None,
                 gameplan_id: str = "") -> dict:
    """Add a phase to a gameplan (appends a section + status rows)."""
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.add_phase(paths, gameplan_id=gid, name=name, goal=goal,
                               depends_on_phases=depends_on_phases)


def cz_transition_phase(phase_n: str, to_status: str, gameplan_id: str = "") -> dict:
    """Advance a phase's lifecycle status so cz_status reflects reality.

    to_status: not_started | ready | in_progress | complete | blocked | failed
    (aliases like start/done/block accepted). Stamps Started/Completed dates.
    Use this at phase boundaries — it's the blessed write for phase status, which
    otherwise has no tool and freezes cz_status at the first phase.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.transition_phase(paths, gameplan_id=gid, phase_n=phase_n,
                                       to_status=to_status)


def cz_add_amendment(title: str, affected_sections: str, affected_phases: str,
                     triggered_by: str, what: str, why: str, gameplan_id: str = "") -> dict:
    """Record a first-class amendment (A-NNN) to a started gameplan."""
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.add_amendment(paths, gameplan_id=gid, title=title,
                                   affected_sections=affected_sections,
                                   affected_phases=affected_phases,
                                   triggered_by=triggered_by, what=what, why=why,
                                   amendments_ritual=config.ritual_enabled("amendments"))


def cz_add_decision(title: str, context: str, decision: str, consequences: str,
                    scope: str = "project", supersedes: str = "", gameplan_id: str = "",
                    evidence: str = "") -> dict:
    """Append an ADR (D-NNN project-wide, or D-k gameplan-internal).

    `evidence` optionally cites the concrete provenance behind the decision
    (commit, file:line, benchmark, doc) as an **Evidence** line in the entry.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.add_decision(paths, title=title, context=context, decision=decision,
                                  consequences=consequences, scope=scope,
                                  gameplan_id=gid, supersedes=supersedes or None,
                                  evidence=evidence or None)


def cz_add_invariant(text: str, introduced_by: str = "") -> dict:
    """Append a project invariant (INVARIANT-NN)."""
    paths, _ = repo_ctx()
    return mutations.add_invariant(paths, text=text, introduced_by=introduced_by or None)


def cz_add_finding(
    title: str,
    severity: str,
    impact: str,
    affected: str = "",
    invariant: str = "",
    preconditions: str = "",
    root_cause: str = "",
    reproduction: str = "",
    recommendation: str = "",
    regression_tests: str = "",
    status: str = "open",
) -> dict:
    """Append a security finding (H-NN) to the append-only HARDENING risk tracker (a.k.a. add_risk).

    Records a structured audit finding: severity + impact are always captured;
    supply affected code, the invariant violated, exploit preconditions, root
    cause, a safe reproduction, the recommended fix, and regression tests as
    available. Findings are append-only — resolve by updating status, not deleting.
    """
    paths, _ = repo_ctx()
    return mutations.add_finding(
        paths, title=title, severity=severity, impact=impact,
        affected=affected, invariant=invariant, preconditions=preconditions,
        root_cause=root_cause, reproduction=reproduction,
        recommendation=recommendation, regression_tests=regression_tests,
        status=status,
    )


def cz_resolve_finding(finding_id: str, status: str = "resolved", note: str = "") -> dict:
    """Update a finding's status + dated resolution note in HARDENING (append-only).

    The tracker's policy is "mark resolved with a date, never delete" — this is the
    blessed write for that, instead of a forbidden hand-edit. e.g.
    cz_resolve_finding("H-03", "resolved", "owner confirmed 3-of-5 Safe").
    """
    paths, _ = repo_ctx()
    return mutations.resolve_finding(paths, finding_id=finding_id, status=status,
                                     note=note or None)


def cz_add_lesson(text: str, category: str = "Process", gameplan_id: str = "",
                  evidence: str = "") -> dict:
    """Add an accumulated lesson (rolls into every future handoff).

    `evidence` optionally cites the concrete provenance that produced the lesson
    (commit, file:line, phase, output id); it renders inline and rides along in
    every handoff rollup.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.add_lesson(paths, gameplan_id=gid, text=text, category=category,
                                evidence=evidence or None)


def cz_consolidate_lessons(numbers: list[int], text: str, category: str = "Process",
                           gameplan_id: str = "") -> dict:
    """Synthesize several overlapping lessons into one (anti-bloat, D-009).

    Adds <text> as a new lesson and marks each source lesson
    "(obsolete: consolidated into #N)" — every future handoff carries one
    line instead of many, and the log keeps the full audit trail. Use when
    the accumulated lessons start repeating themselves.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.consolidate_lessons(paths, gameplan_id=gid, numbers=list(numbers),
                                         text=text, category=category)


def cz_obsolete_lesson(number: str, reason: str = "", gameplan_id: str = "") -> dict:
    """Mark a lesson obsolete so future handoffs stop carrying it.

    Appends the documented "(obsolete <date>: <reason>)" marker — the line
    stays in the log (append-only memory), but the handoff roll-up prunes
    it. Idempotent. number is a gameplan lesson ("4") or a project lesson
    id ("L-04", curating docs/LESSONS.md). This is the blessed write for
    pruning; never hand-edit the lessons list.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.obsolete_lesson(paths, gameplan_id=gid, number=number,
                                     reason=reason or None)


def cz_promote_lesson(number: str, text: str = "", category: str = "",
                      gameplan_id: str = "") -> dict:
    """Promote a gameplan lesson into the project-level docs/LESSONS.md.

    For lessons that should outlive this gameplan: the lesson gets an L-NN
    entry with provenance in a compact project doc that every future
    handoff carries (across gameplans). The source line is marked
    "(promoted <date>: L-NN)" and stops rolling up individually. Optional
    text rewrites the wording (promotion is a chance to distill); category
    defaults to the source lesson's. Typical moment: gameplan close-out.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.promote_lesson(paths, gameplan_id=gid, number=number,
                                    text=text or None, category=category or None)


def cz_add_correction(phase: str, gameplan_said: str, actually: str, why: str,
                      lesson: str = "", gameplan_id: str = "") -> dict:
    """Record a divergence from the gameplan (C-NN); optionally promote a lesson."""
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.add_correction(paths, gameplan_id=gid, phase=phase,
                                    gameplan_said=gameplan_said, actually=actually,
                                    why=why, lesson=lesson or None)


def cz_add_output(phase: str, key: str, value: str, gameplan_id: str = "") -> dict:
    """Record a concrete value a phase produced into the Outputs Registry.

    The registry (PHASE-STATUS.md) is the cross-phase memory for real
    captured values — ids, counts, paths, endpoints — so later phases read
    them instead of guessing or interrupting the user. Upserting the same
    key updates it in place. This is the blessed write; never hand-edit
    the registry.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.add_output(paths, gameplan_id=gid, phase=str(phase),
                                key=key, value=value)


def cz_add_phase_summary(phase: str, text: str, gameplan_id: str = "") -> dict:
    """Record the 1–2 paragraph completion summary for a finished phase.

    Lands under "Per-Phase Completion Summaries" in the handoff index —
    the at-a-glance record of what each phase actually shipped (stuck at
    its scaffold placeholder until this write existed). Re-recording a
    phase's summary replaces it. Typical moment: right after
    cz_transition_phase(..., "complete").
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.add_phase_summary(paths, gameplan_id=gid, phase=str(phase),
                                       text=text)


def cz_upsert_entity(id: str, type: str, version: str = "", status: str = "",
                     depends_on: list[str] | None = None,
                     fields: dict[str, Any] | None = None) -> dict:
    """Create or update a tracked entity doc with valid frontmatter."""
    paths, _ = repo_ctx()
    return mutations.upsert_entity(paths, id=id, type=type, version=version or None,
                                   status=status or None, depends_on=depends_on, fields=fields)


def cz_transition_status(id: str, to_status: str, run_cascade: bool = True) -> dict:
    """Transition an entity's status; fires cascade automatically when enabled."""
    paths, config = repo_ctx()
    result = mutations.transition_status(paths, config, id=id, to_status=to_status,
                                         run_cascade=run_cascade)
    # Flatten the nested cascade result so the tool return stays shallow.
    casc = result.pop("cascade", None)
    if casc:
        result["cascade_report_path"] = casc.get("report_path")
        result["cascade_direct"] = casc.get("direct")
        result["cascade_transitive"] = casc.get("transitive")
    return result


def cz_add_open_item(text: str, phase: str = "", gameplan_id: str = "") -> dict:
    """Record a blocker or cross-phase question as an auto-numbered open item (O-NN).

    The clarify gate's blessed write (D-015): open items get a stable id instead
    of untracked prose, so cz_status reports the unresolved ones and
    cz_transition_phase surfaces them when completing a phase. Optional `phase`
    tags the item for relevance. Resolve with cz_resolve_open_item — items are
    marked resolved, never deleted.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.add_open_item(paths, gameplan_id=gid, text=text, phase=phase or None)


def cz_resolve_open_item(id: str, resolution: str, gameplan_id: str = "") -> dict:
    """Mark an open item (O-NN) resolved in place — never deleted (append-only).

    Appends a "(resolved <date>: <resolution>)" marker to the item's line.
    Idempotent: re-resolving is a no-op. The blessed write for closing an open
    item; never hand-edit the Open Items section.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.resolve_open_item(paths, gameplan_id=gid, id=id, resolution=resolution)


def cz_set_exit_criteria(phase: str, criteria: list[str], gameplan_id: str = "") -> dict:
    """Author or replace a phase's exit criteria as machine-checkable - [ ] items.

    The exit-criteria gate's authoring write (D-015): replaces the phase's "Exit
    criteria" list (placeholder or prior items) with `criteria`, preserving the
    checked state of any item whose text is unchanged. Check items off with
    cz_check_exit_criterion; cz_transition_phase surfaces the unchecked ones when
    completing the phase.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.set_exit_criteria(paths, gameplan_id=gid, phase=phase,
                                       criteria=list(criteria))


def cz_check_exit_criterion(phase: str, criterion: str, checked: bool = True,
                            gameplan_id: str = "") -> dict:
    """Check (or uncheck) one of a phase's exit criteria, matched by substring.

    Idempotent: toggling to the current state is a no-op. The blessed write for
    marking a criterion done; cz_transition_phase to complete surfaces any still
    unchecked (advisory, never blocking — INVARIANT-05).
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.check_exit_criterion(paths, gameplan_id=gid, phase=phase,
                                          criterion=criterion, checked=checked)


# --- the registry ----------------------------------------------------------------


@dataclass(frozen=True)
class Op:
    """One registered operation: the shared callable + whether it writes."""

    fn: Callable[..., dict]
    writes: bool


# Order mirrors tools_list.TOOL_NAMES; the parity test welds them together.
REGISTRY: dict[str, Op] = {
    "cz_status": Op(cz_status, writes=False),
    "cz_next_phase_context": Op(cz_next_phase_context, writes=False),
    "cz_graph_query": Op(cz_graph_query, writes=False),
    "cz_preflight": Op(cz_preflight, writes=True),  # baseline refresh, locked at the write site
    "cz_cascade": Op(cz_cascade, writes=True),
    "cz_resolve_cascade": Op(cz_resolve_cascade, writes=True),
    "cz_write_handoff": Op(cz_write_handoff, writes=True),
    "cz_upsert_entity": Op(cz_upsert_entity, writes=True),
    "cz_transition_status": Op(cz_transition_status, writes=True),
    "cz_add_decision": Op(cz_add_decision, writes=True),
    "cz_add_invariant": Op(cz_add_invariant, writes=True),
    "cz_add_finding": Op(cz_add_finding, writes=True),
    "cz_resolve_finding": Op(cz_resolve_finding, writes=True),
    "cz_add_lesson": Op(cz_add_lesson, writes=True),
    "cz_obsolete_lesson": Op(cz_obsolete_lesson, writes=True),
    "cz_consolidate_lessons": Op(cz_consolidate_lessons, writes=True),
    "cz_promote_lesson": Op(cz_promote_lesson, writes=True),
    "cz_add_correction": Op(cz_add_correction, writes=True),
    "cz_add_output": Op(cz_add_output, writes=True),
    "cz_add_phase_summary": Op(cz_add_phase_summary, writes=True),
    "cz_create_gameplan": Op(cz_create_gameplan, writes=True),
    "cz_add_phase": Op(cz_add_phase, writes=True),
    "cz_transition_phase": Op(cz_transition_phase, writes=True),
    "cz_add_amendment": Op(cz_add_amendment, writes=True),
    "cz_add_open_item": Op(cz_add_open_item, writes=True),
    "cz_resolve_open_item": Op(cz_resolve_open_item, writes=True),
    "cz_set_exit_criteria": Op(cz_set_exit_criteria, writes=True),
    "cz_check_exit_criterion": Op(cz_check_exit_criterion, writes=True),
    "cz_analyze": Op(cz_analyze, writes=False),
    "cz_critique": Op(cz_critique, writes=False),
}


# --- the batch executor ------------------------------------------------------------


def run_batch(batch: list[Any]) -> tuple[list[dict], bool]:
    """Execute ``[{op, args}, ...]`` sequentially; per-op results, overall verdict.

    Each entry yields ``{n, op, ok, result|error}``. A failed op never aborts
    the batch — later ops still run (their results say what happened), and the
    overall verdict is False if anything failed. An op-level ``{"ok": false}``
    return (validation failure) counts as failed, same as an exception
    (LockHeld, bad args, not a clauderized repo).
    """
    results: list[dict] = []
    all_ok = True
    for i, item in enumerate(batch):
        name = item.get("op", "") if isinstance(item, dict) else ""
        args = item.get("args") or {} if isinstance(item, dict) else {}
        entry: dict[str, Any] = {"n": i, "op": name}
        spec = REGISTRY.get(name)
        if not isinstance(item, dict) or not name:
            entry.update(ok=False, error='each item must be {"op": "<cz_*>", "args": {...}}')
        elif spec is None:
            entry.update(ok=False, error=f"unknown op {name!r} — op names are exactly "
                                         f"the cz_* tool names (see tools_list)")
        elif not isinstance(args, dict):
            entry.update(ok=False, error="args must be a JSON object")
        else:
            try:
                result = spec.fn(**args)
                ok = bool(result.get("ok", True)) if isinstance(result, dict) else True
                entry.update(ok=ok, result=result)
            except TypeError as e:
                # Signature mismatch — the schema misuse case.
                entry.update(ok=False, error=f"bad args for {name}: {e}")
            except Exception as e:  # LockHeld, RuntimeError, ... — report, don't crash the batch
                entry.update(ok=False, error=f"{type(e).__name__}: {e}")
        if not entry["ok"]:
            all_ok = False
        results.append(entry)
    return results, all_ok
