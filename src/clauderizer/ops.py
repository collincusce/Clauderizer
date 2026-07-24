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

import functools
import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import contract, listing, mutations, revision
from .config import Config
from .graph import cascade as cascade_mod
from .graph import index, query
from .locking import write_lock
from .paths import RepoPaths, find_repo_root, resolve
from .profiles import detect
from .rituals import handoff, preflight, status_bundle


def repo_ctx() -> tuple[RepoPaths, Config]:
    """Resolve the clauderized repo and its config — shared by every op and resource.

    Discovery is decoupled from the process cwd: when ``$CLAUDERIZER_REPO`` is set
    it names the repo to serve (``clauderizer-mcp --repo`` exports it), else we fall
    back to cwd. That lets a host which cannot set the repo as its process cwd — a
    Windows desktop serving a ``\\\\wsl.localhost`` UNC repo it can't ``cd`` into
    (D-054/D-055) — still point the stateless server at the right repo. The value
    may be any path inside the repo; ``find_repo_root`` walks up to the marker.
    """
    override = os.environ.get("CLAUDERIZER_REPO")
    start = Path(override) if override else Path.cwd()
    root = find_repo_root(start)
    paths = resolve(root)
    if not paths.config_file.exists():
        src = f"$CLAUDERIZER_REPO ({override})" if override else f"cwd ({start})"
        raise RuntimeError(
            f"not a clauderized repo (no .clauderizer/config.toml under {root}, "
            f"resolved from {src}). Run `clauderize init`."
        )
    return paths, Config.load(paths.config_file)


def _graph(paths: RepoPaths):
    return index.load_or_rebuild(paths.docs, paths.index_file)


# --- read / context ops ---------------------------------------------------------


def cz_status() -> dict:
    """Current state: active gameplan, phase table, baseline tests, pending cascades, blockers.

    Also evaluates the focus gameplan's declared standing conditions
    (.clauderizer/conditions.<id>.toml) — a met condition surfaces as
    "iteration proposed", never auto-runs anything.
    """
    paths, config = repo_ctx()
    bundle = status_bundle.compute(paths, config, conditions=True)
    # Long-lived servers only: nudge when the engine source on disk is newer
    # than this process (a fresh CLI/ops process never sees True).
    bundle["engine_stale"] = status_bundle.engine_source_newer_than(
        status_bundle.PROCESS_STARTED)
    return bundle


def cz_next_phase_context(audience: str = "") -> dict:
    """Assemble everything the next/current phase session needs in one call (read-only: returns the handoff text without writing a file).

    Pass audience (e.g. "copywriter") to get that working role's view: lessons
    tagged for other audiences drop out of the bundle, untagged ones stay. The
    written handoff file is never filtered — this shapes only the read-only
    context returned here.
    """
    paths, config = repo_ctx()
    bundle = status_bundle.compute(paths, config)
    target = bundle.get("current_phase") or bundle.get("next_phase")
    if not target or not config.active_gameplan:
        return {"ok": False, "summary": "no active/next phase", "status": bundle}
    result = handoff.assemble(paths, config, config.active_gameplan, target["number"],
                              write=False, audience=audience)
    result["phase"] = target
    result["status_summary"] = bundle.get("summary")
    result["next_action"] = bundle.get("next_action")
    return result


def cz_gameplans(include_closed: bool = False, gameplan_id: str = "") -> dict:
    """List gameplans as a portfolio — the multi-axis view across concurrent
    gameplans. Open ones by default (include_closed=True adds finished ones); each
    card carries kind, lifecycle, the current/next phase, blockers, pending-cascade
    count, and whether it is the focus. Read-only (L-03).

    Pass gameplan_id for that gameplan's DETAIL view: its card plus the
    deliverables board — entities of type=deliverable carrying gameplan: <id>,
    laid out against the kind's lifecycle statuses as `matrix_md`. Deliverables
    are a campaign's execution units (a film, a short, a deck), never the
    individual rendered files they produce.
    """
    paths, config = repo_ctx()
    if gameplan_id:
        from . import kinds as _kinds

        gdir = paths.gameplan_dir(gameplan_id)
        if not (gdir / "GAMEPLAN.md").exists():
            return {"ok": False, "summary": f"unknown gameplan {gameplan_id!r}"}
        card = status_bundle.gameplan_card(gdir, config.focus, paths.kinds_dir)
        kind = _kinds.resolve(card["kind"], paths.kinds_dir)
        delivs = status_bundle.deliverables_for(paths, gameplan_id)
        return {
            "ok": True,
            "gameplan": card,
            "deliverables": delivs,
            "lifecycle": kind.lifecycle,
            "matrix_md": status_bundle.deliverable_matrix_md(delivs, kind.lifecycle),
            "summary": (f"{gameplan_id}: {len(delivs)} deliverable(s)"
                        + (f" across {' → '.join(kind.lifecycle)}"
                           if kind.lifecycle else "")),
        }
    cards = status_bundle.portfolio(paths, config, include_closed=include_closed)
    open_n = sum(1 for c in cards if c["open"])
    return {
        "ok": True,
        "focus": config.focus,
        "gameplans": cards,
        "summary": (
            f"{open_n} open gameplan(s)"
            + (f", {len(cards) - open_n} closed" if include_closed else "")
            + (f"; focus = {config.focus}" if config.focus else "; no focus set")
        ),
    }


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


def cz_get(id: str, kind: str = "auto") -> dict:
    """Fetch one corpus entry's full body by id — the addressable read that makes
    loading a whole corpus file unnecessary.

    cz_analyze hits and the handoff carry an entry's id + a one-line abstract (a
    pointer, not the body — D-013); when the abstract is not enough, cz_get resolves
    the FULL text from canonical markdown on demand. Returns {ok, id, title, body,
    status, anchor, kind}; ok is False when the id is unknown. Works for any corpus
    id — a decision (D-NNN), invariant (INVARIANT-NN), finding (H-NN), or lesson
    (L-NN); `kind` is an optional hint, normally inferred since ids are globally
    unique. Read-only — no write lock on the read path (L-03).
    """
    paths, _ = repo_ctx()
    from . import analyze

    # writes=False means cz_get never mutates CANONICAL markdown (INVARIANT-01).
    # get_entry may still refresh the gitignored disposable abstract-index cache
    # (.clauderizer/abstract_index.json) as any graph read does — same as
    # cz_graph_query; that cache is rebuilt from markdown and safe to discard, so it
    # does not make this a mutating op. (test_cz_get_mutates_no_tracked_markdown.)
    entry = analyze.get_entry(paths, id, kind=kind)
    if entry is None:
        return {"ok": False, "id": id,
                "error": f"no corpus entry with id {id!r} in docs/ "
                         f"(expected a D-/INVARIANT-/H-/L- id)"}
    return {"ok": True, **entry}


def cz_analyze(text: str, k: int = 5) -> dict:
    """Surface the existing decisions/invariants most relevant to `text`, the
    one-hop graph neighbors `text` touches but has not connected, AND the
    plausibly-missing depends_on edges between tracked entities — for you to judge
    contradiction/supersession, gaps, and missing structure (the analyze gate).

    Judgment-based like cz_cascade and read-only: the engine ASSEMBLES candidates
    (relevant entries by keyword + entity-id overlap; the `adjacent` graph entities
    by one-hop structural adjacency; `suggested_edges` = entity pairs with high
    lexical/id overlap and NO edge either way)
    and prompts; it never decides and NEVER auto-writes an edge. Use
    before recording a decision, or to vet a phase/plan against recorded memory. If
    a surfaced entry is contradicted, record a correction or revise; if superseded,
    set `supersedes` on cz_add_decision; if an `adjacent` entity should have been
    accounted for, that is a gap to close; for a `suggested_edges` pair, add the
    real edge with cz_upsert_entity(depends_on=[...]) or dismiss it permanently via
    cz_upsert_entity(fields={'not_related_to': [...]}).

    Each ranked decision/invariant hit also carries a one-line `abstract` (a D-013
    pointer); when it is not enough, call cz_get(id) for that entry's full body.
    """
    paths, config = repo_ctx()
    from . import analyze as _analyze

    res = _analyze.analyze(paths, text, k=k, focus_gameplan=config.active_gameplan or "")
    n = len(res["decisions"]) + len(res["invariants"])
    adj = res.get("adjacent") or []
    edges = res.get("suggested_edges") or []
    res["ok"] = True
    res["prompt"] = (
        "Review against the text. (1) CONTRADICTION/SUPERSESSION: does it contradict "
        "any surfaced decision/invariant (record a correction or revise) or supersede "
        "one (set supersedes on cz_add_decision)? (2) GAPS: the `adjacent` entries are "
        "graph-neighbors of what you're touching that nothing here has connected to "
        "this text — decide whether your change should account for them. (3) MISSING "
        "EDGES: `suggested_edges` are entity pairs with high lexical/id overlap and no "
        "depends_on edge either way — for each, either add the real edge with "
        "cz_upsert_entity(depends_on=[...]) or, if genuinely unrelated, dismiss it for "
        "good by recording cz_upsert_entity(id=<a>, fields={'not_related_to': ['<b>']}). "
        "The engine surfaces candidates only; you decide and it never auto-writes an edge."
    )
    res["summary"] = (
        f"surfaced {n} relevant entr{'y' if n == 1 else 'ies'} "
        f"+ {len(adj)} adjacent + {len(edges)} suggested edge(s) for review"
    )
    return res


def cz_critique(target: str = "") -> dict:
    """Self-critique gate: surface a reference-free Coverage / Coherence /
    Grounding / Self-enhancement / Authority rubric for `target` — a phase
    number, "gameplan" (default), or "handoff" (the current in-progress phase)
    — for YOU to grade.

    Read-only and advisory like cz_analyze: the engine ASSEMBLES the gaps it can
    detect deterministically (unresolved open items, unchecked exit criteria,
    graph drift, pending cascades, lessons lacking provenance) grouped by
    dimension, and prompts; it never scores or blocks. Because the target is
    always self-authored, two further axes flag a self-judge's failure modes:
    Self-enhancement (an item closed by a hollow note, or a completion claim
    that outruns a live gap) and Authority (a lesson whose evidence cites an
    unverifiable source with no in-repo anchor). Reference-free and stdlib-only.
    Run it before completing a phase, before trusting a handoff, or at gameplan
    close.
    """
    paths, config = repo_ctx()
    from .rituals import critique as _critique

    return _critique.critique(paths, config, target=target or None)


def cz_audit() -> dict:
    """Work/release self-audit gate: after a gameplan, audit the WORK PRODUCT and
    release-readiness — distinct from cz_critique, which audits memory coherence.

    Read-only and advisory like cz_analyze/cz_critique (INVARIANT-05): the engine
    ASSEMBLES the deterministic signals it can compute — version single-sourcing
    (pyproject vs the package __version__ vs the top CHANGELOG entry), an
    uncommitted working tree, and unresolved cascades/open items — and prompts a
    judgment checklist for the failure modes a green suite cannot catch: verify in
    a CLEAN environment (not a stale editable install), re-audit every CONSUMER of
    a changed entity (incl. untracked ones), and claim only what you verified. It
    never scores or blocks. Grounded in real misses (D-051); stdlib-only. Run it at
    gameplan close (the shipped clauderizer-close-gameplan skill invokes it).
    """
    paths, config = repo_ctx()
    from .rituals import audit as _audit

    return _audit.audit(paths, config)


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


def _pending_report_for(reports_dir, entity_id: str):
    """The pending cascade report already covering this entity, or None.

    Matches on the entity (the report header's `# Cascade Report: <entity> …`),
    NOT the transition label — a status transition cascades with a "status a ->
    b" label while a hand-typed cz_cascade uses "a -> b", yet both walk the same
    dependents. The trailing space anchors the entity boundary so a prefix like
    `subsys.web` does not match `subsys.web-ui`. This is the F6 duplicate guard.
    """
    from .rituals.status_bundle import pending_cascades

    prefix = f"# Cascade Report: {entity_id} "
    for name in pending_cascades(reports_dir):
        try:
            first = (reports_dir / name).read_text(encoding="utf-8").split("\n", 1)[0]
        except OSError:
            continue
        if first.startswith(prefix):
            return reports_dir / name
    return None


def cz_cascade(entity_id: str, transition: str, dry_run: bool = False) -> dict:
    """Walk the DAG forward from a changed entity and write a cascade report.

    A status change already cascades automatically (cz_transition_status), so
    call this only for a SEPARATE manual edit. If a pending report already
    covers this entity, it is reused — not duplicated (F6); resolve that report
    with cz_resolve_cascade rather than running another cascade for the same
    change.
    """
    paths, config = repo_ctx()
    if not config.active_gameplan:
        return {"ok": False, "error": "no active gameplan for the report dir"}
    g = _graph(paths)
    reports_dir = paths.gameplan_dir(config.active_gameplan) / "_cascade-reports"
    if dry_run:
        res = cascade_mod.run(g, entity_id, transition, reports_dir, dry_run=True)
        res.pop("report_md", None)
        return res
    # F6: don't write a second "needs review" report when one for this entity is
    # already open — the transition that prompted this almost certainly cascaded.
    existing = _pending_report_for(reports_dir, entity_id)
    if existing is not None:
        return {
            "ok": True, "entity_id": entity_id, "transition": transition,
            "report_path": str(existing), "reused": True,
            "summary": (f"reused the pending cascade report already covering {entity_id} "
                        f"({existing.name}) — a status transition already cascades, so resolve "
                        f"that report with cz_resolve_cascade instead of duplicating it"),
        }
    # Report writes serialize with every other tracked write (H-05); this path
    # doesn't route through mutations.*, so lock here.
    with write_lock(paths.write_lock_file):
        res = cascade_mod.run(g, entity_id, transition, reports_dir, dry_run=False)
        # Cross-gameplan fan-out (D10): flag any OTHER open gameplan that declared
        # it consumes this entity (cz_consumes), so its own cascade_hygiene catches it.
        cross = cascade_mod.fanout_cross_gameplan(
            g, entity_id, transition, focus_gid=config.active_gameplan,
            gameplans_root=paths.gameplans)
    # The full report is written to disk; don't dump the whole markdown blob
    # back through the tool result (keeps the return shallow + JSON-clean).
    res.pop("report_md", None)
    if cross:
        res["cross_gameplan_refs"] = cross
        res["summary"] += f"; fanned out to {len(cross)} other gameplan(s)"
    return res


def cz_resolve_cascade(verdicts: dict[str, str] | None = None,
                       updates_applied: str = "", updates_deferred: str = "",
                       report: str = "", gameplan_id: str = "") -> dict:
    """Record the verdicts for a cascade report's "needs review" dependents.

    After cz_cascade flags dependents, decide each one and record it here. To
    CLOSE a report you must do BOTH: (1) give a verdict for every flagged
    dependent — `verdicts` maps entity id -> what was done ("no change needed",
    "updated pin to ^2.0.0", …); AND (2) fill the edit summary — pass
    `updates_applied` (a one-line summary of the concrete edits, or "none" if
    nothing changed) or `updates_deferred`. Recording verdicts alone leaves the
    report pending (which blocks the cascade_hygiene preflight check); the
    result's `summary` then says exactly what is still missing. `report`
    defaults to the most recent pending report. This is the blessed write —
    never hand-edit cascade reports.
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
        result = handoff.assemble(paths, config, gid, phase_n)
        # Telemetry (Phase 0): log which lessons/invariants this handoff surfaced
        # so the signal can later join to the phase outcome. Blessed, write-locked
        # op — never a hook (INVARIANT-06); append-only (INVARIANT-03); read by
        # cz_corpus_health, never auto-acted (INVARIANT-05).
        if result.get("ok"):
            from . import telemetry
            s = handoff.surfaced_ids(paths, gid, phase_n)
            telemetry.record_surfaced(
                paths.telemetry_file, gameplan=gid, phase=phase_n,
                lessons=s["lessons"], invariants=s["invariants"],
                gameplan_lessons=s["gameplan_lessons"])
            result["telemetry"] = "surfaced"
        return result


# --- mutation ops ----------------------------------------------------------------


def cz_create_gameplan(name: str, first_phase: str = "",
                       kind: str = "driven", focus: bool = True) -> dict:
    """Scaffold a new gameplan directory and (by default) make it the focus.

    `kind`: a registered gameplan kind — "driven" (a finite phase DAG with a
    terminal post-mortem), "loop" (a standing iterative maintenance gameplan — see
    GAMEPLAN-PROCEDURE.md "Loop Gameplans"), "campaign" (a creative campaign), or a
    custom kind defined in .clauderizer/kinds/. An unknown kind is rejected with the
    list of known ones.

    `first_phase`: name of the first phase; defaults to the KIND's template first
    phase (driven→Bootstrap, loop→Iterate, campaign→Concept) when left blank.

    `focus` (default True): make the new gameplan the focus. Pass False to create a
    second axis WITHOUT stealing focus from the current one (O-04) — the other open
    gameplans stay exactly where they are; switch later with cz_focus.
    """
    from . import kinds

    paths, config = repo_ctx()
    if not kinds.is_known(kind, paths.kinds_dir):
        known = ", ".join(sorted(kinds.load_all(paths.kinds_dir)))
        return {"ok": False,
                "error": f"unknown kind {kind!r}; known kinds: {known} "
                         f"(define a custom one in .clauderizer/kinds/<name>.toml)"}
    # Template the first phase from the kind when the caller didn't name one.
    first_phase = first_phase or kinds.resolve(kind, paths.kinds_dir).first_phase
    # The scaffold write locks inside mutations.*; the focus config flip must sit
    # in the same critical section (reentrant), or two creators could interleave
    # scaffold and flip.
    with write_lock(paths.write_lock_file):
        result = mutations.create_gameplan(paths, name, first_phase=first_phase, kind=kind)
        if focus:
            config.focus = result["gameplan_id"]
            paths.config_file.write_text(config.to_toml(), encoding="utf-8")
            revision.bump(paths.clauderizer_dir)
    result["focused"] = focus
    result["kind"] = kind
    return result


def cz_focus(gameplan_id: str = "") -> dict:
    """Switch focus — the default-target gameplan for cz_status / do-phase /
    handoff / preflight when no gameplan_id is given — to `gameplan_id`.

    The blessed write for the focus pointer (replaces hand-editing config.toml).
    An empty `gameplan_id` reports the current focus + the open portfolio instead
    of switching. Warns (never blocks) if the target is closed or missing.
    """
    paths, config = repo_ctx()
    if not gameplan_id:
        cards = status_bundle.portfolio(paths, config)
        return {
            "ok": True, "focus": config.focus, "gameplans": cards,
            "summary": (f"focus = {config.focus}" if config.focus else "no focus set")
                       + f"; {len(cards)} open gameplan(s)",
        }
    gdir = paths.gameplan_dir(gameplan_id)
    if not (gdir / "GAMEPLAN.md").exists():
        return {"ok": False,
                "error": f"no gameplan {gameplan_id!r} on disk "
                         f"(docs/gameplans/{gameplan_id}/GAMEPLAN.md not found)"}
    card = status_bundle.gameplan_card(gdir, gameplan_id, paths.kinds_dir)
    prev = config.focus
    # The focus flip is a tracked write; serialize with every other writer (H-05).
    with write_lock(paths.write_lock_file):
        config.focus = gameplan_id
        paths.config_file.write_text(config.to_toml(), encoding="utf-8")
        revision.bump(paths.clauderizer_dir)
    result = {"ok": True, "focus": gameplan_id, "previous_focus": prev,
              "summary": f"focus {prev or '(none)'} -> {gameplan_id}"}
    if not card["open"]:
        result["warning"] = (
            f"{gameplan_id} is {card['lifecycle']} (closed) — you focused a finished "
            f"gameplan; pick an open one with cz_gameplans or start one with "
            f"cz_create_gameplan")
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


def cz_add_invariant(text: str, introduced_by: str = "", scope: str = "project",
                     audience: str = "") -> dict:
    """Append an invariant (INVARIANT-NN) — project-wide by default.

    Pass scope="gameplan:<id>" when the rule belongs to one gameplan (a
    campaign's brand rules, say) so other gameplans' context stays free of it,
    and an optional audience label (e.g. "copywriter") when only one working
    role needs it. If the text strongly overlaps an existing invariant the
    result carries a `related_invariants` list + an `advisory` suggesting a
    scoped entry instead of a global re-declaration — advisory only, the entry
    is still appended.
    """
    paths, _ = repo_ctx()
    return mutations.add_invariant(paths, text=text, introduced_by=introduced_by or None,
                                   scope=scope or "project", audience=audience or None)


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
                  evidence: str = "", audience: str = "") -> dict:
    """Add an accumulated lesson (rolls into every future handoff).

    `evidence` optionally cites the concrete provenance that produced the lesson
    (commit, file:line, phase, output id); it renders inline and rides along in
    every handoff rollup. `audience` optionally tags the lesson for one working
    role (e.g. "copywriter", "art-director", "coder") so audience-filtered
    handoffs carry only what that role needs; untagged lessons reach everyone.

    If the new lesson strongly overlaps an existing PROJECT lesson, the result carries
    a `related_lessons` list + an `advisory` nudging consolidation
    (cz_consolidate_lessons) instead of appending — advisory only, never blocks.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    return mutations.add_lesson(paths, gameplan_id=gid, text=text, category=category,
                                evidence=evidence or None, audience=audience or None)


def cz_consolidate_lessons(numbers: list[int], text: str, category: str = "Process",
                           gameplan_id: str = "") -> dict:
    """Synthesize several overlapping lessons into one (anti-bloat).

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


def cz_register_skill(name: str, description: str, source: str = "",
                      category: str = "General") -> dict:
    """Register an Agent Skill into docs/SKILLS.md so the project is skill-aware.

    Skills are line-entries mirroring promoted lessons; every future handoff
    surfaces the relevant ones (Phase 2). `source` cites where the SKILL.md
    lives. Idempotent on `name`. Confirm a cz_discover_skills proposal with this.
    """
    paths, _ = repo_ctx()
    return mutations.register_skill(paths, name=name, description=description,
                                    source=source or None, category=category)


def cz_obsolete_skill(skill_id: str, reason: str = "") -> dict:
    """Mark a registered skill (S-NN) obsolete in docs/SKILLS.md — never delete.

    The blessed write for pruning a skill no longer available/relevant; the
    handoff roll-up stops carrying it. Idempotent.
    """
    paths, _ = repo_ctx()
    return mutations.obsolete_skill(paths, skill_id=skill_id, reason=reason or None)


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


def cz_consumes(consumes: list[str], gameplan_id: str = "") -> dict:
    """Declare that a gameplan CONSUMES tracked entities produced elsewhere — the
    cross-gameplan dependency edge (D10).

    Upserts a `gameplan.<gid>` graph node whose depends_on UNIONS the given entity
    ids, so transitioning or cascading any of them flags THIS gameplan as a
    dependent — and the cascade fans a pending cross-ref into its _cascade-reports
    even when another gameplan has focus. Sugar over cz_upsert_entity(id=
    'gameplan.<gid>', type='gameplan', depends_on=[...]); call again to add more
    (the list accumulates). Use for an artifact built by one axis (e.g. a tool from
    the code gameplan) that another axis (e.g. a campaign) relies on.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    node_id = f"gameplan.{gid}"
    g = _graph(paths)
    node = g.get(node_id)
    existing = [str(p.target) for p in node.depends_on] if node else []
    merged = list(dict.fromkeys(existing + list(consumes)))  # union, order-stable
    res = mutations.upsert_entity(paths, id=node_id, type="gameplan", depends_on=merged)
    res["gameplan"] = gid
    res["consumes"] = merged
    res["summary"] = f"{node_id} consumes {len(merged)} entit(y/ies): {', '.join(merged)}"
    return res


def cz_transition_status(id: str, to_status: str, run_cascade: bool = True) -> dict:
    """Transition an entity's status; fires cascade automatically when enabled.

    This is also how you RETIRE an entity: transition it to `retired` (or
    `obsolete`) instead of deleting its file. The entity stays in the graph for
    history but is demoted in relevance surfacing — the sanctioned, append-only
    alternative to hand-removing a tracked doc.
    """
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

    The clarify gate's blessed write: open items get a stable id instead
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

    The exit-criteria gate's authoring write: replaces the phase's "Exit
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
    unchecked (advisory, never blocking).
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.check_exit_criterion(paths, gameplan_id=gid, phase=phase,
                                          criterion=criterion, checked=checked)


def cz_modernize(apply: bool = False) -> dict:
    """Report — and with apply=true, perform — the corpus-modernization pass.

    The procedure version is the methodology document's own version line —
    separate from the engine's package version (engine 1.4.x carries
    procedure 1.5.x). The default is a read-only report: the MECHANICAL
    updates a newer engine would apply (the config's procedure-version stamp
    and migrations, missing preflight-gate example files, a stale engine-owned
    copy of the procedure doc) plus ADVISORY proposals for memory-shaped gaps — declared QA gates with
    no wired command, near-duplicate invariants that look scope-taggable,
    campaign gameplans without deliverable entities, loop gameplans without
    standing conditions. apply=true performs only the mechanical tier;
    decisions, invariants, lessons, findings, and gameplan memory are never
    auto-edited — each proposal names the normal cz_* write that would act on
    it, and the choice stays yours.
    """
    paths, config = repo_ctx()
    from . import modernize
    from . import proposals as _proposals

    if apply:
        return modernize.apply(paths, config)
    rep = modernize.report(paths, config)
    led = _proposals.load_ledger(paths)
    all_props = rep["proposals"]
    pending = _proposals.filter_pending(all_props, led)
    suppressed = len(all_props) - len(pending)
    rep["proposals"] = pending
    rep["pending_count"] = len(pending)
    rep["suppressed_count"] = suppressed
    rep["summary"] = (
        f"{len(rep['mechanical'])} mechanical update(s) available, "
        f"{len(pending)} advisory proposal(s) pending"
        + (f" ({suppressed} dismissed/deferred)" if suppressed else "")
    )
    return rep


def cz_dismiss_proposal(proposal_id: str) -> dict:
    """Dismiss an advisory proposal (modernize or dream) by its ``id`` — it
    will NOT re-surface (in cz_modernize/cz_dream or the session digest) until
    it materially changes and hashes to a new id. Recorded in a per-user,
    gitignored ledger (.clauderizer/proposals.local.toml); this is a personal
    "seen it", not a team-wide gate off-switch (D-052/D-059). Get ids from
    cz_modernize or cz_dream's blocked_on_triage state."""
    paths, _ = repo_ctx()
    from . import proposals as _proposals

    return _proposals.dismiss(paths, proposal_id)


def cz_defer_proposal(proposal_id: str, days: int = 7) -> dict:
    """Snooze an advisory proposal (modernize or dream) by its ``id`` for
    ``days`` days (default 7); it re-surfaces after that — and a deferred dream
    proposal stops gating cz_dream until then. Per-user, gitignored ledger
    (D-052/D-059). Get ids from cz_modernize or cz_dream."""
    paths, _ = repo_ctx()
    from . import proposals as _proposals

    return _proposals.defer(paths, proposal_id, days)


def cz_onboard() -> dict:
    """Assemble the onboarding bundle for an existing project — read-only.

    Returns the Clauderizer docs that are still scaffold placeholders
    (`unseeded`), the repo's existing documentation that likely holds project
    knowledge (`candidates` — README, root design/spec files, and docs/*.md the
    engine doesn't own; paths and sizes only), and a `prompt` describing how to
    seed memory from them: rewrite the placeholder prose docs directly, record
    real subsystems/features with cz_upsert_entity, and record decisions/rules
    already in force with cz_add_decision/cz_add_invariant citing the source
    file. The engine detects and prompts; it never seeds anything itself. Run
    it again after seeding — seeded docs drop out.
    """
    paths, _ = repo_ctx()
    from . import onboard

    return onboard.report(paths)


def cz_approve_gate(phase: str, criterion: str, note: str = "",
                    gameplan_id: str = "") -> dict:
    """Record a human approval on an APPROVAL exit criterion, bound to the
    artifact's content hash.

    An approval criterion reads `APPROVAL: <artifact-path> — <description>` in a
    phase's exit criteria. Approving computes the artifact's sha256 and stamps it
    into the criterion; every later read recomputes it, so editing the artifact
    makes the approval report "stale" (and the criterion unsatisfied) until it is
    re-approved — surfaced everywhere, enforced nowhere. Re-approving replaces
    the stamp. `note` optionally records who/what approved.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or config.active_gameplan
    if not gid:
        return {"ok": False, "error": "no gameplan specified or active"}
    return mutations.approve_gate(paths, gameplan_id=gid, phase=phase,
                                  criterion=criterion, note=note)


def _default_transcripts_dir() -> str:
    """Best-effort path to this project's Claude Code transcripts (``*.jsonl``).

    Honors $CLAUDERIZER_TRANSCRIPTS_DIR; else derives the slug Claude Code uses
    (~/.claude/projects/<path-with-non-alnum→dashes>), then falls back to a
    projects subdir whose name ends with the repo dir name. Returns "" when it
    cannot resolve — e.g. WSL-from-Windows, where the transcript tree is keyed by
    the Windows path (invisible here) and the caller passes the dir explicitly.
    """
    import os
    import re as _re

    env = os.environ.get("CLAUDERIZER_TRANSCRIPTS_DIR")
    if env:
        return env
    projects = Path.home() / ".claude" / "projects"
    if not projects.exists():
        return ""
    try:
        root = find_repo_root(Path.cwd())
    except Exception:
        return ""
    cand = projects / _re.sub(r"[^A-Za-z0-9]+", "-", str(root))
    if cand.exists():
        return str(cand)
    for p in sorted(projects.glob("*")):
        if p.is_dir() and p.name.endswith(root.name):
            return str(p)
    return ""


def cz_mine_failures(transcripts_dir: str = "", max_proposals: int = 40) -> dict:
    """Mine Claude Code session transcripts for failure→fix patterns and PROPOSE
    draft corrections/lessons (the Headroom `headroom learn` analog).

    Read-only and advisory like cz_analyze/cz_critique: the engine scans the
    transcript JSONL and SURFACES candidates — a tool error then a same-tool
    success, a pytest fail→pass, or a short explicit user correction — and never
    writes. Confirm a genuine proposal by recording it through cz_add_correction
    (or cz_add_lesson); discard the rest. `transcripts_dir` defaults to this
    project's Claude Code transcript directory (set $CLAUDERIZER_TRANSCRIPTS_DIR,
    or pass it explicitly when auto-resolution fails). Deterministic, stdlib-only,
    no enable/disable flag.
    """
    from . import learn

    d = transcripts_dir.strip() or _default_transcripts_dir()
    if not d or not Path(d).exists():
        return {
            "ok": False,
            "error": f"transcripts dir not found: {d or '(unresolved)'}",
            "hint": "pass transcripts_dir (the ~/.claude/projects/<slug> path) "
                    "or set $CLAUDERIZER_TRANSCRIPTS_DIR",
        }
    by_file = learn.mine_dir(d)
    proposals = [{**p, "source": fname}
                 for fname, props in by_file.items() for p in props]
    capped = proposals[:max_proposals]
    return {
        "ok": True,
        "transcripts_dir": str(d),
        "files_scanned": len(by_file),
        "proposal_count": len(proposals),
        "shown": len(capped),
        "proposals": capped,
        "prompt": ("Each proposal is a DRAFT, not a write. For genuine failure→fix "
                   "patterns, confirm and record via cz_add_correction (or "
                   "cz_add_lesson); discard the rest. The engine proposes; you decide."),
        "summary": (f"mined {len(proposals)} failure→fix proposal(s) from "
                    f"{len(by_file)} transcript(s)"
                    + (f"; showing {len(capped)}" if len(capped) < len(proposals) else "")),
    }


def cz_corpus_health() -> dict:
    """Surface a deterministic health snapshot of the lesson corpus + telemetry.

    Read-only and advisory: active project-lesson count, a lexical
    near-duplicate redundancy estimate (no ML), how many active lessons
    have never been surfaced in a handoff, and the surfacing/outcome counts from
    the append-only telemetry log (.clauderizer/telemetry.jsonl). The empirical
    baseline that lesson-utility scoring and the curator read; the agent
    decides what to consolidate/promote/obsolete.
    """
    from . import telemetry

    paths, _ = repo_ctx()
    return telemetry.corpus_health(paths)


def cz_lesson_health() -> dict:
    """Surface per-lesson empirical health from telemetry: utility (fraction of a
    lesson's resolved surfacings that preceded a passing phase), failure-risk,
    surfaced/resolved counts, and an advisory per-lesson signal (never-surfaced /
    low-utility / promotion-candidate). Read-only, deterministic,
    no ML. The input the curator turns into proposed
    consolidate/promote/obsolete actions; the agent decides.
    """
    from . import telemetry

    paths, _ = repo_ctx()
    return telemetry.lesson_health(paths)


def cz_curate() -> dict:
    """PROPOSE a corpus-maintenance batch from telemetry-derived health, read-only
    like cz_mine_failures: consolidate redundant lessons, obsolete never-surfaced
    or low-utility ones, flag high-failure-risk ones for review, and promote
    high-utility gameplan lessons. Each proposal carries evidence + the blessed
    cz_* op to apply it; the agent confirms. No writes, no ML.
    """
    from . import telemetry

    paths, config = repo_ctx()
    return telemetry.curate_proposals(paths, config.active_gameplan)


def cz_loop_step() -> dict:
    """Run one iteration of a loop gameplan (read-only): the convergence metric
    (corpus_health), the curator's proposals, a `converged` flag, and an
    escape-hatch `spawn_gameplan` suggestion for structural work. The agent applies
    the actionable proposals via blessed cz_* writes and calls this again until
    converged. No writes, no ML.
    """
    from . import telemetry

    paths, config = repo_ctx()
    result = telemetry.loop_step(paths, config.active_gameplan)
    # Standing conditions (D3): the loop's threshold triggers, evaluated lazily
    # right where an iteration would begin. Met -> proposed, never auto-run.
    from .rituals import conditions as _conditions

    conds = _conditions.evaluate(paths, config.active_gameplan or "")
    if conds:
        result["standing_conditions"] = conds
        met = [c["name"] for c in conds if c["met"]]
        if met:
            result["iteration_proposed"] = True
            result["summary"] = (str(result.get("summary", "")).rstrip(".")
                                 + f"; standing condition(s) met: {', '.join(met)}"
                                   " — iteration proposed").lstrip("; ")
    # Dream signal (D-059): the loop's iteration body includes the dreaming
    # ritual, so surface where it stands — quiet when the journal is empty.
    from . import dreams as _dreams

    _dp = _dreams.pending_proposals(paths)
    _un = len(_dreams.unconsumed_notes(paths))
    if _dp:
        result["dream"] = {"state": "blocked_on_triage", "pending": len(_dp)}
        result["summary"] = (str(result.get("summary", "")).rstrip(".")
                             + f"; {len(_dp)} dream proposal(s) await triage "
                               "(clauderizer-dream skill)")
    elif _un >= _dreams.RIPENESS_NOTES:
        result["dream"] = {"state": "ripe", "unconsumed": _un}
        result["summary"] = (str(result.get("summary", "")).rstrip(".")
                             + f"; dream ripe ({_un} notes — cz_dream)")
    elif _un:
        result["dream"] = {"state": "not_ripe", "unconsumed": _un,
                           "ripeness": _dreams.RIPENESS_NOTES}
    return result


def cz_discover_skills() -> dict:
    """PROPOSE Agent Skills present in this project's environment but not yet
    registered in docs/SKILLS.md — read-only, like cz_curate / cz_mine_failures.

    Scans the well-known local skill directories (the project's and the user's
    skill folders, plus Clauderizer's own shipped skills), parses each SKILL.md's
    name + description, and diffs against what's already registered. Confirm
    genuine proposals via cz_register_skill; the engine proposes, you decide.
    No writes, no network (external-skill ingestion is out).
    """
    paths, _ = repo_ctx()
    from . import skill_discovery

    return skill_discovery.discover(paths)


# --- listing reads (PhaseKeep m0 asks O-02..O-16; see listing.py) ---------------


def cz_list_open_items(gameplan_id: str = "", include_resolved: bool = True) -> dict:
    """List every tracked open item (O-NN) as a full record across the portfolio.

    Fields: gameplan, id, phase tag, text (markers stripped), resolved,
    resolved_date, resolution. Filter with gameplan_id / include_resolved=False.
    """
    paths, _config = repo_ctx()
    items = listing.open_items(paths, gameplan_id, include_resolved)
    return {"ok": True, "items": items,
            "summary": f"{len(items)} open item(s)"}


def cz_list_decisions(include_bodies: bool = False) -> dict:
    """List the project decision log (D-NNN) with supersession links both ways.

    Renders chains as chains: each record carries supersedes / superseded_by /
    status / date / scope. Bodies on request (include_bodies=True); cz_get
    fetches one by id.
    """
    paths, _config = repo_ctx()
    entries = listing.decisions(paths, include_bodies)
    return {"ok": True, "decisions": entries,
            "summary": f"{len(entries)} decision(s)"}


def cz_list_invariants(include_bodies: bool = False) -> dict:
    """List the invariant register (INVARIANT-NN) with scope and audience tags."""
    paths, _config = repo_ctx()
    entries = listing.invariants(paths, include_bodies)
    return {"ok": True, "invariants": entries,
            "summary": f"{len(entries)} invariant(s)"}


def cz_list_findings(include_bodies: bool = False) -> dict:
    """List the hardening/risk register (H-NN) with lifecycle status."""
    paths, _config = repo_ctx()
    entries = listing.findings(paths, include_bodies)
    return {"ok": True, "findings": entries,
            "summary": f"{len(entries)} finding(s)"}


def cz_list_lessons(gameplan_id: str = "") -> dict:
    """List the lesson corpus with curation state (active/obsolete/promoted).

    Project lessons (L-NN) plus the focus gameplan's accumulated lessons
    (pass gameplan_id for another gameplan's). Each record carries origin,
    category, state, audience, and evidence.
    """
    paths, config = repo_ctx()
    entries = listing.lessons(paths, config, gameplan_id)
    return {"ok": True, "lessons": entries,
            "summary": f"{len(entries)} lesson(s)"}


def cz_list_corrections(gameplan_id: str = "") -> dict:
    """List the correction log (C-NN) as structured records, portfolio-wide by default."""
    paths, _config = repo_ctx()
    entries = listing.corrections(paths, gameplan_id)
    return {"ok": True, "corrections": entries,
            "summary": f"{len(entries)} correction(s)"}


def cz_list_amendments(gameplan_id: str = "") -> dict:
    """List gameplan amendments (A-NNN) as structured records."""
    paths, _config = repo_ctx()
    entries = listing.amendments(paths, gameplan_id)
    return {"ok": True, "amendments": entries,
            "summary": f"{len(entries)} amendment(s)"}


def cz_phase_detail(gameplan_id: str = "") -> dict:
    """Every gameplan's full phase table with exit-criteria state, approvals,
    dates, handoff path, goal, and assignment.

    The read behind gameplan drill-in and reconciliation views: per-criterion
    checked state, computed approval satisfaction (stale/missing/unapproved/
    approved via content hash), and Started/Completed cells — for EVERY
    gameplan, not just the focus. Filter with gameplan_id.
    """
    paths, config = repo_ctx()
    gameplans = listing.phase_detail(paths, config, gameplan_id)
    return {"ok": True, "gameplans": gameplans,
            "summary": f"{len(gameplans)} gameplan(s)"}


def cz_list_cascade_reports(gameplan_id: str = "", include_resolved: bool = True) -> dict:
    """List cascade reports as data: trigger, per-dependent verdicts, pending state.

    The graph view's cascade overlay: what changed, what was flagged, what
    verdict each dependent received — same pending predicate as the digest.
    """
    paths, _config = repo_ctx()
    reports = listing.cascade_reports(paths, gameplan_id, include_resolved)
    return {"ok": True, "reports": reports,
            "summary": f"{len(reports)} cascade report(s)"}


def cz_docs_index() -> dict:
    """Index the canonical documents: docs/*.md, the procedure, every handoff
    and post-mortem — names are the ids cz_doc accepts."""
    paths, _config = repo_ctx()
    docs = listing.docs_index(paths)
    return {"ok": True, "docs": docs, "summary": f"{len(docs)} doc(s)"}


def cz_doc(name: str) -> dict:
    """One canonical document's body, frontmatter-stripped — the front-door doc
    read (external clients never parse repo files; INVARIANT-01 on their side)."""
    paths, _config = repo_ctx()
    return listing.doc(paths, name)


def cz_assignments(gameplan_id: str = "") -> dict:
    """The assignment surface in one read: manager role, per-gameplan default
    assignees, per-phase overrides (O-02 provisional shape)."""
    paths, config = repo_ctx()
    result = listing.assignments(paths, config, gameplan_id)
    result["ok"] = True
    result["summary"] = (f"manager={result['manager'] or '(none)'}; "
                         f"{len(result['gameplans'])} gameplan(s)")
    return result


def cz_assign(gameplan_id: str = "", phase: str = "", assignee: str = "",
              role: str = "") -> dict:
    """Record an assignment: gameplan default, phase override, or the manager role.

    Forms: role='manager' + assignee sets the per-project manager (config);
    gameplan_id + assignee sets the gameplan default (> Assignee: header);
    gameplan_id + phase + assignee sets a phase override (**Assigned**: line).
    Empty assignee clears the target. Provisional shape (proposal 16.7),
    revisitable when PhaseKeep m3 builds the first consumer.
    """
    paths, config = repo_ctx()
    gid = gameplan_id or (config.active_gameplan if not role else "")
    return mutations.assign(paths, gameplan_id=gid or "", phase=phase,
                            assignee=assignee, role=role)


def cz_revision() -> dict:
    """The monotonic memory revision (epoch + counter) — the change signal.

    The near-free poll path is reading .clauderizer/revision.json directly
    (blessed contract surface); this op is the transport-uniform read for
    clients already speaking the registry.
    """
    paths, _config = repo_ctx()
    rec = revision.read(paths.clauderizer_dir)
    return {"ok": True,
            "revision": rec,
            "summary": (f"revision {rec['revision']} (epoch {rec['epoch']})"
                        if rec else "no revision recorded yet (no writes since upgrade)")}


def cz_add_dream(kind: str, note: str, refs: list[str] | None = None,
                 gameplan: str = "", phase: str = "") -> dict:
    """Append one dream note — the per-exchange experiential capture (D-058).

    After each substantive exchange, record 2-4 sentences of what only the
    responding agent could observe. ``kind``: friction (something fought you),
    gap (a memory/doc hole), surprise (an expectation violated), correction
    (the user corrected course), drift (procedure/ritual drifted from the doc),
    win (something worked notably well). ``refs`` names related ids (e.g.
    ["D-058", "L-50", "feat.dream-loop"]). Notes are PII-free by construction —
    no emails, secret tokens, or absolute home paths (the write REJECTS them;
    use repo-relative paths and id references). The journal is local-only
    (.clauderizer/dreams.jsonl — gitignored, append-only); the dreamer later
    mines it into advisory proposals (D-059). ``gameplan``/``phase`` default to
    the active gameplan's current phase. Duplicate content is a safe no-op.
    """
    paths, config = repo_ctx()
    gid = gameplan or (config.active_gameplan or "")
    ph = str(phase or "")
    if not ph and gid:
        rows = status_bundle._phase_rows(paths.gameplan_dir(gid))
        # Fallback order mirrors the digest's "current phase": the in-progress
        # row, else the first not-yet-started one. Tables never store "ready" —
        # that state is computed — so match not_started (dogfood catch: two
        # Phase-4 notes landed with phase="" when the transition was skipped).
        cur = (next((r for r in rows if r.status == "in_progress"), None)
               or next((r for r in rows if r.status in ("ready", "not_started")), None))
        ph = cur.number if cur else ""
    return mutations.add_dream(paths, gameplan=gid, phase=ph, kind=kind,
                               note=note, refs=refs)


def cz_dream(today: str = "") -> dict:
    """Assemble the dream bundle — read-only, gated (D-059, A-001).

    Returns one of three states. ``blocked_on_triage``: previously staged dream
    proposals await triage — handle/dismiss/defer them first; dreaming never
    piles new proposals onto unactioned ones. ``not_ripe``: fewer unconsumed
    notes than the ripeness floor — keep capturing (cz_add_dream). ``ripe``: a
    BOUNDED bundle (top clusters via the canonical tokenizer, exemplar-only
    full text, corpus-health + lesson flags + one-hop graph adjacency for
    entity refs, self-reported est_tokens) for the AGENT to judge into staged
    proposals — the engine assembles, it never decides (INVARIANT-05). Pass
    ``today`` (YYYY-MM-DD) only to pin determinism in tests/replays.
    """
    paths, _config = repo_ctx()
    from . import dreams as _dreams

    return _dreams.assemble(paths, today=today or None)


def cz_dream_propose(proposals: list[dict], reviewed_note_ids: list[str] | None = None) -> dict:
    """Stage the dreamer's judged proposals durably and consume the mined notes.

    ``proposals``: list of {detail (required, <=600 chars, PII-free),
    op? (a blessed cz_* op the handler would run), args? (its arguments),
    evidence? (the dream-note ids behind it)}. Each gets a stable content-hash
    id (``dreamprop:<12-hex>``) — restaging identical content is a no-op, so an
    interrupted dreaming pass is safe to re-run. ``reviewed_note_ids``: ALL note
    ids the pass reviewed (the bundle clusters' note_ids), including clusters
    judged not durable — they are consumed too so they never re-ripen; evidence
    ids are always consumed. Proposals are appended BEFORE the watermark
    advances (crash-safe ordering). Pass proposals=[] with reviewed_note_ids to
    record a "dreamed, nothing durable" pass. Staged proposals surface in the
    session-start pending count and gate cz_dream until triaged
    (cz_handle_dream_proposal / cz_dismiss_proposal / cz_defer_proposal).
    """
    paths, _config = repo_ctx()
    return mutations.stage_dream_proposals(paths, proposals=proposals,
                                           reviewed_note_ids=reviewed_note_ids)


def cz_handle_dream_proposal(proposal_id: str) -> dict:
    """Mark a dream proposal handled AFTER doing its work via the normal blessed
    writes (the suggested op/args, or your better judgment) — appends the
    terminal marker so it leaves the pending set and stops gating cz_dream.
    Dismiss/defer instead when the proposal should NOT be acted on
    (cz_dismiss_proposal / cz_defer_proposal — same ledger as modernize)."""
    paths, _config = repo_ctx()
    return mutations.handle_dream_proposal(paths, proposal_id=proposal_id)


def cz_register_dream_schedule(method: str, cadence: str = "", command: str = "") -> dict:
    """Record how the dreaming loop runs on this machine, retiring the
    session-start plea (A-004). Call it right AFTER creating the real schedule:
    ``method`` e.g. "claude-code-routine", "cron", or "manual" (a legitimate
    "I run /clauderizer-dream myself" verdict — the loop, gauges, and skill
    stay fully active); ``cadence`` e.g. "daily 07:00"; ``command`` the exact
    scheduled command if any. Per-user, gitignored self-report
    (.clauderizer/dreams.schedule.toml) — the engine cannot see crontabs or
    host routines, so this is the honest detection substrate. An empty
    ``method`` clears the record and the plea returns when notes accumulate.
    """
    paths, _config = repo_ctx()
    return mutations.register_dream_schedule(paths, method=method,
                                             cadence=cadence, command=command)


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
    "cz_gameplans": Op(cz_gameplans, writes=False),
    "cz_graph_query": Op(cz_graph_query, writes=False),
    "cz_get": Op(cz_get, writes=False),
    "cz_preflight": Op(cz_preflight, writes=True),  # baseline refresh, locked at the write site
    "cz_cascade": Op(cz_cascade, writes=True),
    "cz_resolve_cascade": Op(cz_resolve_cascade, writes=True),
    "cz_write_handoff": Op(cz_write_handoff, writes=True),
    "cz_upsert_entity": Op(cz_upsert_entity, writes=True),
    "cz_consumes": Op(cz_consumes, writes=True),
    "cz_transition_status": Op(cz_transition_status, writes=True),
    "cz_add_decision": Op(cz_add_decision, writes=True),
    "cz_add_invariant": Op(cz_add_invariant, writes=True),
    "cz_add_finding": Op(cz_add_finding, writes=True),
    "cz_resolve_finding": Op(cz_resolve_finding, writes=True),
    "cz_add_lesson": Op(cz_add_lesson, writes=True),
    "cz_obsolete_lesson": Op(cz_obsolete_lesson, writes=True),
    "cz_consolidate_lessons": Op(cz_consolidate_lessons, writes=True),
    "cz_promote_lesson": Op(cz_promote_lesson, writes=True),
    "cz_register_skill": Op(cz_register_skill, writes=True),
    "cz_obsolete_skill": Op(cz_obsolete_skill, writes=True),
    "cz_add_correction": Op(cz_add_correction, writes=True),
    "cz_add_output": Op(cz_add_output, writes=True),
    "cz_add_phase_summary": Op(cz_add_phase_summary, writes=True),
    "cz_create_gameplan": Op(cz_create_gameplan, writes=True),
    "cz_focus": Op(cz_focus, writes=True),
    "cz_add_phase": Op(cz_add_phase, writes=True),
    "cz_transition_phase": Op(cz_transition_phase, writes=True),
    "cz_add_amendment": Op(cz_add_amendment, writes=True),
    "cz_add_open_item": Op(cz_add_open_item, writes=True),
    "cz_resolve_open_item": Op(cz_resolve_open_item, writes=True),
    "cz_set_exit_criteria": Op(cz_set_exit_criteria, writes=True),
    "cz_check_exit_criterion": Op(cz_check_exit_criterion, writes=True),
    "cz_approve_gate": Op(cz_approve_gate, writes=True),
    "cz_modernize": Op(cz_modernize, writes=True),
    "cz_dismiss_proposal": Op(cz_dismiss_proposal, writes=True),
    "cz_defer_proposal": Op(cz_defer_proposal, writes=True),
    "cz_onboard": Op(cz_onboard, writes=False),
    "cz_analyze": Op(cz_analyze, writes=False),
    "cz_critique": Op(cz_critique, writes=False),
    "cz_audit": Op(cz_audit, writes=False),
    "cz_mine_failures": Op(cz_mine_failures, writes=False),
    "cz_corpus_health": Op(cz_corpus_health, writes=False),
    "cz_lesson_health": Op(cz_lesson_health, writes=False),
    "cz_curate": Op(cz_curate, writes=False),
    "cz_loop_step": Op(cz_loop_step, writes=False),
    "cz_discover_skills": Op(cz_discover_skills, writes=False),
    "cz_list_open_items": Op(cz_list_open_items, writes=False),
    "cz_list_decisions": Op(cz_list_decisions, writes=False),
    "cz_list_invariants": Op(cz_list_invariants, writes=False),
    "cz_list_findings": Op(cz_list_findings, writes=False),
    "cz_list_lessons": Op(cz_list_lessons, writes=False),
    "cz_list_corrections": Op(cz_list_corrections, writes=False),
    "cz_list_amendments": Op(cz_list_amendments, writes=False),
    "cz_phase_detail": Op(cz_phase_detail, writes=False),
    "cz_list_cascade_reports": Op(cz_list_cascade_reports, writes=False),
    "cz_docs_index": Op(cz_docs_index, writes=False),
    "cz_doc": Op(cz_doc, writes=False),
    "cz_assignments": Op(cz_assignments, writes=False),
    "cz_revision": Op(cz_revision, writes=False),
    "cz_assign": Op(cz_assign, writes=True),
    "cz_add_dream": Op(cz_add_dream, writes=True),
    "cz_dream": Op(cz_dream, writes=False),
    "cz_dream_propose": Op(cz_dream_propose, writes=True),
    "cz_handle_dream_proposal": Op(cz_handle_dream_proposal, writes=True),
    "cz_register_dream_schedule": Op(cz_register_dream_schedule, writes=True),
}

# Every op result carries the external contract version (O-05): stamped here,
# at the single dispatch table both transports share, so the CLI ops runner,
# the MCP server, and direct Python callers of REGISTRY entries emit identical
# payloads. functools.wraps keeps each op's signature/docstring visible to
# op_schema and the MCP layer (both follow __wrapped__).


def _stamped(fn: Callable[..., dict]) -> Callable[..., dict]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return contract.stamp(fn(*args, **kwargs))
    return wrapper


REGISTRY = {name: Op(_stamped(spec.fn), spec.writes) for name, spec in REGISTRY.items()}


def run_op(name: str, **kwargs) -> dict:
    """Execute one registered op through the stamped dispatch table.

    The blessed entry point for in-process callers (the CLI verbs): module-level
    functions like ``cz_status`` are the UNSTAMPED originals, so calling them
    directly would emit payloads without ``schema_version`` and silently fork
    the contract surface.
    """
    return REGISTRY[name].fn(**kwargs)


# --- introspection: the no-MCP discoverability surface (F4) ----------------------
# The op functions' signatures + docstrings ARE the contract (the same REGISTRY the
# MCP server registers), so `clauderize ops --list/--schema` reads them directly —
# there is no second schema to drift.


def _op_summary(fn: Callable[..., dict]) -> str:
    """The first sentence of an op's docstring — its one-line summary."""
    doc = inspect.getdoc(fn) or ""
    para = doc.split("\n\n", 1)[0].replace("\n", " ").strip()
    head = para.split(". ", 1)[0].rstrip(".")
    return head[:140]


def op_schema(name: str) -> dict | None:
    """One op's arg schema, introspected from its signature — or None if unknown.

    ``required`` = positional-or-keyword params with no default; ``optional`` = the
    rest, each with its default; ``*args``/``**kwargs`` are skipped. Defaults are
    coerced to JSON-serializable values so the schema round-trips through ``ops``.
    """
    spec = REGISTRY.get(name)
    if spec is None:
        return None
    required: list[str] = []
    optional: list[dict] = []
    for pname, p in inspect.signature(spec.fn).parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is inspect.Parameter.empty:
            required.append(pname)
        else:
            d = p.default
            if not isinstance(d, (str, int, float, bool, type(None))):
                d = repr(d)  # keep the schema JSON-serializable
            optional.append({"name": pname, "default": d})
    return {"op": name, "writes": spec.writes, "summary": _op_summary(spec.fn),
            "required": required, "optional": optional}


def list_ops() -> list[dict]:
    """Every op as ``{op, writes, summary, required}`` — the source for
    ``clauderize ops --list`` and any other op-discovery (F4)."""
    out: list[dict] = []
    for name in REGISTRY:
        sch = op_schema(name)
        assert sch is not None  # name comes straight from REGISTRY
        out.append({"op": name, "writes": sch["writes"],
                    "summary": sch["summary"], "required": sch["required"]})
    return out


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
            entry.update(ok=False, error=f"unknown op {name!r} — run "
                                         f"'clauderize ops --list' for all op names, or "
                                         f"'clauderize ops --schema <op>' for one op's args")
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
