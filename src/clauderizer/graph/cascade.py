"""Post-hoc cascade: walk the DAG forward after a change, render a report.

Per the procedure, cascade is *judgment-based*: this engine finds and reports
the dependents that *might* be affected and marks each "needs review". It does
not pretend to decide whether each dependent is truly affected — that's the
agent's call, filled into the report. This is the deliberate division of labor
that keeps cascade honest rather than faking automation.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from . import query
from .. import revision
from .index import Graph

# Statuses that make an entity a SHAKY foundation: its dependents may rest on
# something that no longer holds, so cascade flags them preemptively (Phase 3 —
# the cascade-walk analogue of SkillOps' risk propagation). Advisory (INVARIANT-05).
_SHAKY_STATUSES = {"superseded", "deprecated", "blocked", "retired", "obsolete"}


def render_report(
    graph: Graph,
    entity_id: str,
    transition: str,
    *,
    now: datetime | None = None,
    phase: str | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    direct = query.dependents(graph, entity_id)
    transitive = [d for d in query.transitive_dependents(graph, entity_id) if d not in direct]
    violations = [v for v in query.pin_violations(graph) if v.target == entity_id]

    lines = [
        f"# Cascade Report: {entity_id} {transition}",
        "",
        f"> Generated: {ts}",
    ]
    if phase:
        lines.append(f"> Phase: {phase}")
    lines += [
        "",
        "## Trigger",
        "",
        f"`{entity_id}` — {transition}",
        "",
        "## Affected entities",
        "",
        "### Direct dependents",
        "",
    ]
    if direct:
        for d in direct:
            ent = graph.get(d)
            status = ent.status if ent else "?"
            lines.append(f"- **{d}** (status: {status}) — checked: _needs review_")
    else:
        lines.append("- _(none)_")
    lines += ["", "### Transitive dependents", ""]
    if transitive:
        for d in transitive:
            lines.append(f"- **{d}** — flagged via upstream; checked: _needs review_")
    else:
        lines.append("- _(none)_")

    if violations:
        lines += ["", "### Semver pin violations", ""]
        for v in violations:
            lines.append(f"- **{v.dependent}** pins `{v.constraint}` — {v.reason}")

    ent = graph.get(entity_id)
    if ent is not None and ent.status in _SHAKY_STATUSES:
        lines += ["", "### Preemptive risk", "",
                  f"`{entity_id}` is **{ent.status}** — dependents may rest on a "
                  "foundation that no longer holds; verify each before relying on it:"]
        flagged = [(d, "direct") for d in direct] + [(d, "transitive") for d in transitive]
        if flagged:
            for d, rel in flagged:
                lines.append(f"- **{d}** ({rel}) — verify it still holds now that "
                             f"`{entity_id}` is {ent.status}")
        else:
            lines.append("- _(no dependents)_")

    lines += [
        "",
        "## Updates applied",
        "",
        "_(fill in concrete edits made to each affected entity, or 'no change needed')_",
        "",
        "## Updates deferred",
        "",
        "_(anything flagged but not yet acted on, with reason + follow-up)_",
        "",
    ]
    return "\n".join(lines)


def _cross_ref_report(entity_id: str, transition: str, source_gid: str,
                      other_gid: str, now: datetime) -> str:
    """A pending cross-gameplan cascade cross-ref dropped into a CONSUMING
    gameplan's report dir. Carries the same `_needs review_` / fill-in markers a
    normal report does, so that gameplan's own cascade_hygiene flags it until its
    session resolves it (cz_resolve_cascade with a verdict for gameplan.<gid>)."""
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return "\n".join([
        f"# Cascade Report: {entity_id} {transition} (cross-gameplan)",
        "",
        f"> Generated: {ts}",
        f"> Source gameplan: {source_gid}",
        "",
        "## Trigger",
        "",
        f"`{entity_id}` — {transition} (changed while gameplan `{source_gid}` had focus)",
        "",
        f"This gameplan (`gameplan.{other_gid}`) declares it CONSUMES `{entity_id}` "
        "(cross-gameplan dependency). Verify whether the change affects this axis.",
        "",
        "## Affected entities",
        "",
        "### Direct dependents",
        "",
        f"- **gameplan.{other_gid}** (consumer) — checked: _needs review_",
        "",
        "## Updates applied",
        "",
        "_(fill in concrete edits made to each affected entity, or 'no change needed')_",
        "",
        "## Updates deferred",
        "",
        "_(anything flagged but not yet acted on, with reason + follow-up)_",
        "",
    ])


def fanout_cross_gameplan(
    graph: Graph,
    entity_id: str,
    transition: str,
    *,
    focus_gid: str | None,
    gameplans_root: Path,
    now: datetime | None = None,
) -> list[str]:
    """Walk the cascade ACROSS gameplans (D10). For every ``gameplan.<gid>`` node
    that depends on ``entity_id`` and is NOT the focus gameplan, drop a pending
    cross-ref into that gameplan's ``_cascade-reports`` so its own cascade_hygiene
    surfaces the change on the other axis. Returns the cross-ref paths written.

    The focus gameplan already gets the normal report from ``run`` — this only
    fans out to the OTHER open axes that declared consumption (cz_consumes)."""
    now = now or datetime.now(timezone.utc)
    written: list[str] = []
    for dep in sorted(set(query.transitive_dependents(graph, entity_id))):
        if not dep.startswith("gameplan."):
            continue
        other_gid = dep.split(".", 1)[1]
        if other_gid == focus_gid:
            continue
        gdir = gameplans_root / other_gid
        if not gdir.is_dir():
            continue
        reports_dir = gdir / "_cascade-reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        path = reports_dir / report_filename(entity_id, now, reports_dir)
        path.write_text(
            _cross_ref_report(entity_id, transition, focus_gid or "(none)", other_gid, now),
            encoding="utf-8")
        revision.bump_for(path)
        written.append(str(path))
    return written


def report_filename(entity_id: str, now: datetime | None = None,
                    reports_dir: Path | None = None) -> str:
    """Name a cascade report: ``YYYY-MM-DD-<entity>-NN.md``.

    The zero-padded ``-NN`` sequence disambiguates same-day cascades of one
    entity, which previously overwrote each other silently (gameplan D4 of
    engine-structural-robustness; discipline-seams lesson #5). The sequence —
    never a timestamp — keeps names deterministic and lexicographically
    chronological within a day. Legacy unsuffixed reports keep their names
    and count as sequence 0, so the next report beside one is ``-01``.
    """
    now = now or datetime.now(timezone.utc)
    safe = entity_id.replace("/", "-").replace(" ", "-")
    stem = f"{now.strftime('%Y-%m-%d')}-{safe}"
    seq = 1
    if reports_dir is not None and reports_dir.exists():
        pat = re.compile(rf"^{re.escape(stem)}(?:-(\d+))?\.md$")
        for p in reports_dir.iterdir():
            m = pat.match(p.name)
            if m:
                seq = max(seq, int(m.group(1) or 0) + 1)
    return f"{stem}-{seq:02d}.md"


def run(
    graph: Graph,
    entity_id: str,
    transition: str,
    reports_dir: Path,
    *,
    dry_run: bool = False,
    now: datetime | None = None,
    phase: str | None = None,
) -> dict:
    """Render and (unless ``dry_run``) write a cascade report.

    Returns a structured result describing what was found and where it went.
    """
    now = now or datetime.now(timezone.utc)
    report_md = render_report(graph, entity_id, transition, now=now, phase=phase)
    direct = query.dependents(graph, entity_id)
    transitive = [d for d in query.transitive_dependents(graph, entity_id) if d not in direct]
    path = reports_dir / report_filename(entity_id, now, reports_dir)
    written = False
    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(report_md, encoding="utf-8")
        revision.bump_for(path)
        written = True
    return {
        "ok": True,
        "entity_id": entity_id,
        "transition": transition,
        "direct": direct,
        "transitive": transitive,
        "report_md": report_md,
        "report_path": str(path),
        "written": written,
        "summary": (
            f"cascade {entity_id} {transition}: "
            f"{len(direct)} direct, {len(transitive)} transitive dependents"
        ),
    }
