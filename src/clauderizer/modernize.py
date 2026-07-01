"""Corpus modernization (D-042): a versioned, two-tier upgrade pass.

When the engine moves ahead of a repo's corpus, the improvements should reach
the repo "automatically in the general sense": the MECHANICAL tier — engine-owned
scaffolds and config migrations, all git-diffable — auto-applies on
``clauderize upgrade`` / ``cz_modernize(apply=true)``, while the MEMORY tier is
only ever SURFACED as advisory proposals for the agent to act on with the normal
blessed writes (INVARIANT-05). Nothing here ever edits DECISIONS.md,
INVARIANTS.md, LESSONS.md, HARDENING.md, or any gameplan directory — the only
docs write is refreshing the engine-owned GAMEPLAN-PROCEDURE.md copy. Detection
is read-only and cheap; the status digest carries at most one modernization line
(D-027/INVARIANT-08), driven by the config's ``procedure_version`` stamp alone.
"""

from __future__ import annotations

import re

from . import PROCEDURE_VERSION, assets, kinds
from .config import Config
from .markdown import writer
from .paths import RepoPaths

_PROC_DOC_VER_RE = re.compile(r"\*\*Procedure version\*\*\s*:?\s*(\d+)\.(\d+)\.(\d+)")

# Gate names that are structural or profile-backed rather than user-wired.
_NON_WIRED_GATES = frozenset({
    "branch_base", "clean_tree", "deps_spotcheck", "branch_creation",
    "cascade_hygiene", "handoff_presence", "tests", "build",
})


def _ver_tuple(v: str) -> tuple[int, int, int]:
    try:
        a, b, c = (int(x) for x in v.split("."))
        return a, b, c
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _procedure_doc_version(paths: RepoPaths) -> str | None:
    p = paths.procedure_file
    if not p.exists():
        return None
    m = _PROC_DOC_VER_RE.search(p.read_text(encoding="utf-8"))
    return ".".join(m.groups()) if m else None


def _open_gameplan_kinds(paths: RepoPaths, config: Config) -> dict[str, str]:
    """``{gameplan_id: kind}`` for every OPEN gameplan (derived, never stored)."""
    from .rituals import status_bundle

    return {c["id"]: c["kind"]
            for c in status_bundle.portfolio(paths, config) if c["open"]}


def _wireable_gates(kind: kinds.Kind) -> list[str]:
    return [c for c in kind.preflight_checks if c not in _NON_WIRED_GATES]


def _example_body(kind_name: str, gates: list[str]) -> str:
    lines = [
        f"# Preflight gate wiring for kind '{kind_name}'.",
        f"# Copy this file to preflight.{kind_name}.toml and give each gate a real",
        "# shell command — a gate passes when its command exits 0. Until wired,",
        "# the declared gate warns at preflight time instead of silently skipping.",
        "#",
        "[gates]",
    ]
    lines += [f'# {g} = "<your shell command — exit 0 = pass>"' for g in gates]
    return "\n".join(lines) + "\n"


def _near_dup_invariant_pairs(paths: RepoPaths, limit: int = 5) -> list[tuple]:
    """Active-invariant pairs over the near-dup threshold — the scope-tag
    candidates (D-043). Same canonical tokenizer + threshold as every other
    similarity computation (INVARIANT-09)."""
    from . import analyze
    from .graph import abstract_index

    recs = [r for r in abstract_index.build(paths)["entries"].values()
            if r.get("kind") == "invariant"
            and str(r.get("status") or "active").lower() == "active"]
    out: list[tuple] = []
    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            a, b = set(recs[i]["token_set"]), set(recs[j]["token_set"])
            union = a | b
            if not union:
                continue
            jac = len(a & b) / len(union)
            if jac >= analyze._LESSON_DUP_JACCARD:
                out.append((recs[i]["id"], recs[j]["id"], round(jac, 3)))
    out.sort(key=lambda t: (-t[2], t[0]))
    return out[:limit]


def report(paths: RepoPaths, config: Config) -> dict:
    """The read-only modernization report: what apply WOULD do (mechanical tier)
    plus the advisory memory-tier proposals. Never writes anything."""
    mechanical: list[dict] = []
    stamp = config.procedure_version or ""
    if stamp != PROCEDURE_VERSION:
        mechanical.append({
            "action": "stamp_procedure_version",
            "detail": f"config stamp {stamp or '(unstamped legacy corpus)'} "
                      f"→ {PROCEDURE_VERSION}"})
    try:
        raw_cfg = paths.config_file.read_text(encoding="utf-8")
    except OSError:
        raw_cfg = ""
    if "[active_gameplan]" in raw_cfg:
        mechanical.append({
            "action": "migrate_config_focus",
            "detail": "legacy [active_gameplan] section → [focus] (1.2.0 migration)"})
    if not (paths.clauderizer_dir / "kinds").exists():
        mechanical.append({
            "action": "ensure_kinds_overlay_dir",
            "detail": ".clauderizer/kinds/ (per-repo custom-kind overlays)"})
    open_kinds = _open_gameplan_kinds(paths, config)
    for kind_name in sorted(set(open_kinds.values())):
        kind = kinds.resolve(kind_name, paths.kinds_dir)
        gates = _wireable_gates(kind)
        if not gates:
            continue
        wired = paths.clauderizer_dir / f"preflight.{kind_name}.toml"
        example = paths.clauderizer_dir / f"preflight.{kind_name}.toml.example"
        if not wired.exists() and not example.exists():
            mechanical.append({
                "action": f"scaffold_preflight_example:{kind_name}",
                "detail": f".clauderizer/preflight.{kind_name}.toml.example "
                          f"(gates: {', '.join(gates)})"})
    doc_ver = _procedure_doc_version(paths)
    if doc_ver is not None and _ver_tuple(doc_ver) < _ver_tuple(PROCEDURE_VERSION):
        mechanical.append({
            "action": "refresh_procedure_doc",
            "detail": f"engine-owned GAMEPLAN-PROCEDURE.md copy v{doc_ver} "
                      f"→ v{PROCEDURE_VERSION}"})

    proposals: list[dict] = []
    from .rituals import conditions as conditions_mod
    from .rituals import status_bundle
    from .rituals.preflight import _load_preflight_gates

    for gid, kind_name in sorted(open_kinds.items()):
        kind = kinds.resolve(kind_name, paths.kinds_dir)
        gates = _wireable_gates(kind)
        if gates:
            unwired = [g for g in gates if g not in _load_preflight_gates(paths, kind_name)]
            if unwired:
                proposals.append({
                    "kind": "unwired_gates", "gameplan": gid,
                    "detail": f"kind '{kind_name}' declares QA gates with no wired "
                              f"command ({', '.join(unwired)}) — wire [gates] in "
                              f".clauderizer/preflight.{kind_name}.toml so preflight "
                              "runs your real checks instead of warning"})
        if kind.lifecycle and not status_bundle.deliverables_for(paths, gid):
            proposals.append({
                "kind": "no_deliverables", "gameplan": gid,
                "detail": f"'{gid}' tracks no deliverable entities — record each "
                          "execution unit with cz_upsert_entity(type='deliverable', "
                          f"fields={{'gameplan': '{gid}'}}) to get the "
                          "deliverables board (cz_gameplans gameplan_id=...)"})
        if kind_name == "loop" and not conditions_mod.load_conditions(paths, gid):
            proposals.append({
                "kind": "no_standing_conditions", "gameplan": gid,
                "detail": f"loop gameplan '{gid}' declares no standing conditions — "
                          f"declare threshold probes in .clauderizer/conditions.{gid}.toml "
                          "so status can propose iterations when they trip"})
    for a, b, jac in _near_dup_invariant_pairs(paths):
        proposals.append({
            "kind": "near_dup_invariants",
            "detail": f"{a} and {b} strongly overlap (Jaccard {jac}) — if one "
                      "restates a single gameplan's rule, record future ones with "
                      "scope='gameplan:<id>' (D-043); append-only history stays"})

    return {
        "ok": True,
        "engine_procedure": PROCEDURE_VERSION,
        "corpus_procedure": stamp or None,
        "stale": bool(mechanical),
        "mechanical": mechanical,
        "proposals": proposals,
        "summary": (f"{len(mechanical)} mechanical update(s) available, "
                    f"{len(proposals)} advisory proposal(s)"),
    }


def apply(paths: RepoPaths, config: Config) -> dict:
    """Apply the MECHANICAL tier only; proposals remain proposals.

    By construction this writes only: the config file (stamp + focus migration
    via one to_toml rewrite), .clauderizer/ scaffold files, and the engine-owned
    GAMEPLAN-PROCEDURE.md copy. Memory docs and gameplan directories are never
    touched (D-042; INVARIANT-03/05)."""
    rep = report(paths, config)
    applied: list[str] = []
    rewrite_config = False
    for item in rep["mechanical"]:
        act = item["action"]
        if act in ("stamp_procedure_version", "migrate_config_focus"):
            rewrite_config = True
        elif act == "ensure_kinds_overlay_dir":
            (paths.clauderizer_dir / "kinds").mkdir(parents=True, exist_ok=True)
        elif act.startswith("scaffold_preflight_example:"):
            kind_name = act.split(":", 1)[1]
            kind = kinds.resolve(kind_name, paths.kinds_dir)
            example = paths.clauderizer_dir / f"preflight.{kind_name}.toml.example"
            writer.refuse_if_symlink(example)
            example.parent.mkdir(parents=True, exist_ok=True)
            example.write_text(_example_body(kind_name, _wireable_gates(kind)),
                               encoding="utf-8")
        elif act == "refresh_procedure_doc":
            writer.refuse_if_symlink(paths.procedure_file)
            paths.procedure_file.write_text(assets.procedure_text(), encoding="utf-8")
        applied.append(act)
    if rewrite_config:
        config.procedure_version = PROCEDURE_VERSION
        writer.refuse_if_symlink(paths.config_file)
        paths.config_file.write_text(config.to_toml(), encoding="utf-8")
    return {
        "ok": True,
        "engine_procedure": PROCEDURE_VERSION,
        "applied": applied,
        "proposals": rep["proposals"],
        "summary": (f"applied {len(applied)} mechanical update(s); "
                    f"{len(rep['proposals'])} advisory proposal(s) remain "
                    "(memory is yours to edit — see each proposal's cz_* suggestion)"),
    }
