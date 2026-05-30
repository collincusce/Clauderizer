"""Post-hoc cascade: walk the DAG forward after a change, render a report.

Per the procedure, cascade is *judgment-based*: this engine finds and reports
the dependents that *might* be affected and marks each "needs review". It does
not pretend to decide whether each dependent is truly affected — that's the
agent's call, filled into the report. This is the deliberate division of labor
that keeps cascade honest rather than faking automation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import query
from .index import Graph


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


def report_filename(entity_id: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    safe = entity_id.replace("/", "-").replace(" ", "-")
    return f"{now.strftime('%Y-%m-%d')}-{safe}.md"


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
    path = reports_dir / report_filename(entity_id, now)
    written = False
    if not dry_run:
        reports_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(report_md, encoding="utf-8")
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
