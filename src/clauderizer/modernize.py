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


def _stamp_would_regress(stamp: str) -> bool:
    """H-30: True when the repo's stamp is NEWER than this engine's procedure —
    stamping would ratchet the version backward (a stale serving engine on an
    ahead-of-publish tree). An unparseable stamp reads as legacy (0,0,0),
    never as newer, so junk still stamps forward."""
    return _ver_tuple(stamp) > _ver_tuple(PROCEDURE_VERSION)


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


def report(paths: RepoPaths, config: Config, *, cheap: bool = False) -> dict:
    """The read-only modernization report: what apply WOULD do (mechanical tier)
    plus the advisory memory-tier proposals. Never writes anything.

    Each advisory proposal carries a stable ``id`` (D-052) so it can be triaged
    (dismissed/deferred) and re-identified across runs. ``cheap=True`` skips the
    only expensive detector — the near-duplicate-invariant scan, which builds the
    abstract index — so the status digest can compute a pending count without the
    cost (the near-dup proposals are simply omitted from a cheap report)."""
    from . import proposals as _proposals
    mechanical: list[dict] = []
    skew_proposal: dict | None = None
    stamp = config.procedure_version or ""
    if stamp != PROCEDURE_VERSION:
        if _stamp_would_regress(stamp):
            # H-30: a stale serving engine never ratchets the stamp backward —
            # observed live when the published-engine MCP restamped 1.11.0 down
            # to 1.9.0. The skew surfaces for judgment instead (INVARIANT-05).
            skew_proposal = {
                "kind": "engine_older_than_stamp",
                "id": _proposals.proposal_id("engine_older_than_stamp",
                                             stamp, PROCEDURE_VERSION),
                "detail": f"this engine's procedure ({PROCEDURE_VERSION}) is "
                          f"older than the repo's stamp ({stamp}) — not "
                          "regressing the stamp; run the repo's newer engine "
                          "(e.g. its venv CLI) to modernize, or upgrade this "
                          "install"}
        else:
            mechanical.append({
                "action": "stamp_procedure_version",
                "detail": f"procedure stamp {stamp or '(unstamped legacy corpus)'} "
                          f"→ {PROCEDURE_VERSION} (the methodology version this "
                          "engine carries — not the engine's package version)"})
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
    missing_modules = _missing_manifest_modules(config)
    if missing_modules:
        mechanical.append({
            "action": "ensure_modules_current",
            "detail": f"{len(missing_modules)} doc module(s) this engine's "
                      f"'{config.size or 'standard'}' manifest carries that this "
                      f"corpus does not ({', '.join(missing_modules)}) — the "
                      "shipped stanza and skills reference them by path; "
                      "scaffolded only if absent, never clobbered"})
    missing_ignores = _missing_local_state_ignores(paths)
    if missing_ignores:
        mechanical.append({
            "action": "ensure_gitignore_current",
            "detail": f"{len(missing_ignores)} per-machine path(s) not gitignored "
                      f"({', '.join(missing_ignores[:3])}"
                      + (", …" if len(missing_ignores) > 3 else "") + ") — D-067"})
    doc_ver = _procedure_doc_version(paths)
    if doc_ver is not None and _ver_tuple(doc_ver) < _ver_tuple(PROCEDURE_VERSION):
        mechanical.append({
            "action": "refresh_procedure_doc",
            "detail": f"engine-owned GAMEPLAN-PROCEDURE.md copy v{doc_ver} "
                      f"→ v{PROCEDURE_VERSION}"})

    proposals: list[dict] = []
    if skew_proposal is not None:
        proposals.append(skew_proposal)
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
                    "id": _proposals.proposal_id("unwired_gates", gid, *sorted(unwired)),
                    "detail": f"kind '{kind_name}' declares QA gates with no wired "
                              f"command ({', '.join(unwired)}) — wire [gates] in "
                              f".clauderizer/preflight.{kind_name}.toml so preflight "
                              "runs your real checks instead of warning"})
        if kind.lifecycle and not status_bundle.deliverables_for(paths, gid):
            proposals.append({
                "kind": "no_deliverables", "gameplan": gid,
                "id": _proposals.proposal_id("no_deliverables", gid),
                "detail": f"'{gid}' tracks no deliverable entities — record each "
                          "execution unit with cz_upsert_entity(type='deliverable', "
                          f"fields={{'gameplan': '{gid}'}}) to get the "
                          "deliverables board (cz_gameplans gameplan_id=...)"})
        if kind_name == "loop" and not conditions_mod.load_conditions(paths, gid):
            proposals.append({
                "kind": "no_standing_conditions", "gameplan": gid,
                "id": _proposals.proposal_id("no_standing_conditions", gid),
                "detail": f"loop gameplan '{gid}' declares no standing conditions — "
                          f"declare threshold probes in .clauderizer/conditions.{gid}.toml "
                          "so status can propose iterations when they trip"})
    # Onboarding gap (D-044): the repo has real documentation while the
    # scaffolded Clauderizer docs are still placeholders — every already-
    # clauderized repo learns about onboarding at its next upgrade.
    from . import onboard as onboard_mod

    unseeded = onboard_mod.unseeded_docs(paths)
    if unseeded:
        cands = onboard_mod.spec_candidates(paths)
        if cands:
            shown = ", ".join(unseeded[:4]) + ("…" if len(unseeded) > 4 else "")
            proposals.append({
                "kind": "unseeded_docs",
                "id": _proposals.proposal_id("unseeded_docs", *sorted(unseeded)),
                "detail": f"{len(unseeded)} Clauderizer doc(s) are still scaffold "
                          f"placeholders ({shown}) while {len(cands)} existing "
                          f"doc(s) look like specs (e.g. {cands[0]['path']}) — run "
                          "cz_onboard (or the clauderizer-onboard skill) to seed "
                          "memory from them; the engine never seeds for you"})

    # A per-repo overlay of a packaged kind pins that kind's capability set to
    # whatever the overlay declares — an overlay written before the packaged
    # kind gained a deliverable lifecycle silently overrides the lifecycle
    # away. The overlay is user-authored, so this is a proposal, never an edit.
    packaged = kinds.load_all(None)
    for kind_name in sorted(set(open_kinds.values())):
        pk = packaged.get(kind_name)
        if not pk or not pk.lifecycle:
            continue
        overlay = (paths.kinds_dir / f"{kind_name}.toml") if paths.kinds_dir else None
        if (overlay and overlay.exists()
                and not kinds.resolve(kind_name, paths.kinds_dir).lifecycle):
            statuses = ", ".join(f'"{s}"' for s in pk.lifecycle)
            proposals.append({
                "kind": "stale_kind_overlay",
                "id": _proposals.proposal_id("stale_kind_overlay", kind_name),
                "detail": f".clauderizer/kinds/{kind_name}.toml predates the packaged "
                          f"'{kind_name}' kind's deliverable lifecycle and overrides it "
                          f"away — add a [lifecycle] table (statuses = [{statuses}]) to "
                          "the overlay, or delete the overlay if it no longer customizes "
                          "anything, to enable deliverable tracking"})
    for a, b, jac in ([] if cheap else _near_dup_invariant_pairs(paths)):
        proposals.append({
            "kind": "near_dup_invariants",
            "id": _proposals.proposal_id("near_dup_invariants", a, b),
            "detail": f"{a} and {b} strongly overlap (Jaccard {jac}) — if one "
                      "restates a single gameplan's rule, record future ones with "
                      "scope='gameplan:<id>' (D-043); append-only history stays"})

    # O-05: every generated proposal is self-explanatory — the payload names
    # what the flagged thing IS; the report names what dismiss/defer MEAN.
    for p in proposals:
        p.setdefault("what", _proposals.WHAT.get(p.get("kind", ""), ""))
    return {
        "ok": True,
        "engine_procedure": PROCEDURE_VERSION,
        "corpus_procedure": stamp or None,
        "stale": bool(mechanical),
        "mechanical": mechanical,
        "proposals": proposals,
        "triage": _proposals.TRIAGE_SEMANTICS,
        "summary": (f"{len(mechanical)} mechanical update(s) available, "
                    f"{len(proposals)} advisory proposal(s)"),
    }


#: Engine-owned per-machine state that must never be committed (D-067). Single
#: source for `init`, `upgrade` and the doctor nudge, so the three cannot drift.
LOCAL_STATE_IGNORES = (
    ".clauderizer/index.json",
    ".clauderizer/abstract_index.json",
    ".clauderizer/proposals.local.toml",
    ".clauderizer/telemetry.jsonl",
    ".clauderizer/dreams.jsonl",
    ".clauderizer/dreams.schedule.toml",
    ".clauderizer/proposals.dream.jsonl",
    ".clauderizer/dreams.watermark.json",
    ".clauderizer/revision.json",
    ".clauderizer/hook.sh",
    ".clauderizer/hook.cmd",
    ".clauderizer/write.lock",
    ".clauderizer/baseline.json",
    # P1's session evidence + refusal journal were gitignored by init but never
    # joined this tier-1 list, so existing repos could not converge on them —
    # the exact gap D-067's "ships as a tier-1 action" rule exists to prevent.
    ".clauderizer/sessions.jsonl",
    ".clauderizer/refusals.jsonl",
    # D-073: seen-vs-open engagement receipts.
    ".clauderizer/seen.local.jsonl",
)


def _missing_manifest_modules(config: Config) -> list[str]:
    """Manifest doc modules for this repo's size that its config does not carry.

    The same D-042 TIER-1 reasoning as ``ensure_gitignore_current``, one level
    up: a release that adds a doc module to ``SIZE_MANIFESTS`` reaches only
    FRESH inits. ``config.merge_missing`` keeps the repo's existing non-empty
    ``modules`` list and ``init`` scaffolds from ``config.modules`` alone, so an
    already-inited repo keeps the old set forever while the refreshed stanza and
    shipped skills reference the new docs by path — the L-65 dangling-claim
    class, delivered to every install in the world that already ran ``init``
    (measured live on a 1.13.0 → 2.0.0 walk: GLOSSARY + ENFORCEMENT referenced
    by CLAUDE.md/AGENTS.md and the fleet skill, present in neither).

    Purely additive: modules are appended, never removed, and the doc itself is
    only written when absent (no content is ever clobbered). Stated trade-off:
    the manifest is the size's contract, so a module a user deliberately
    *deleted* from their list is re-added — as one visible, git-diffable line
    that ``upgrade --report`` shows before anything is written.
    """
    from . import assets
    from .config import SIZE_MANIFESTS

    manifest = SIZE_MANIFESTS.get(config.size or "standard",
                                  SIZE_MANIFESTS["standard"])
    have = set(config.modules)
    return [m for m in manifest["modules"]
            if m not in have and assets.doc_template(m) is not None]


_DOC_REF_RE = re.compile(r"docs/([A-Z][A-Z0-9_-]*)\.md")

# Docs the engine ships a template for but deliberately does NOT scaffold: they
# are created on demand by a blessed write (cz_add_lesson, cz_register_skill),
# so their absence in a repo is correct, not a dangling pointer.
ON_DEMAND_DOCS = frozenset({"LESSONS", "SKILLS"})


def engine_doc_references() -> dict[str, list[str]]:
    """``{DOC_NAME: [referencing engine artifact, ...]}`` for every
    ``docs/<NAME>.md`` the engine's OWN wiring names.

    Sources are engine-owned only — the shipped stanza template and the shipped
    skills — so a reference in the user's own prose is never second-guessed.
    """
    from . import assets

    sources: list[tuple[str, str]] = []
    try:
        sources.append(("the shipped stanza",
                        assets.template_text("claude_stanza.md")))
    except OSError:  # pragma: no cover - template ships in the wheel
        pass
    for d in assets.skill_dirs():
        try:
            sources.append((f"skill {d.name}",
                            (d / "SKILL.md").read_text(encoding="utf-8")))
        except OSError:  # pragma: no cover
            continue
    refs: dict[str, list[str]] = {}
    for label, text in sources:
        for name in sorted(set(_DOC_REF_RE.findall(text))):
            refs.setdefault(name, []).append(label)
    return refs


def dangling_doc_pointers(paths: RepoPaths,
                          config: Config) -> list[tuple[str, str]]:
    """``(referencing artifact, missing doc)`` for every doc the engine's own
    wiring names, that this repo's size manifest promises to scaffold, and that
    is nonetheless absent (L-65's detector).

    D-069: a discipline the engine asks for needs a machine-checked signal that
    notices when it has not been performed. "Never ship a pointer to a file that
    is not there" was recorded as a lesson, fixed for fresh init, and stayed
    broken on the upgrade path — with ``doctor`` printing a green
    "corpus modernized" line over it on a repo whose stanza pointed at two
    missing files. Scoped to the manifest so an ON_DEMAND_DOCS reference (a
    repo that simply has no lessons yet) is never flagged. Read-only.
    """
    from .config import SIZE_MANIFESTS

    manifest = set(SIZE_MANIFESTS.get(config.size or "standard",
                                      SIZE_MANIFESTS["standard"])["modules"])
    promised = manifest | set(config.modules)
    out: list[tuple[str, str]] = []
    for name, labels in engine_doc_references().items():
        if name in ON_DEMAND_DOCS or name not in promised:
            continue
        if not paths.doc(name).exists():
            out += [(label, f"{paths.docs.name}/{name}.md") for label in labels]
    return sorted(set(out))


def _missing_local_state_ignores(paths: RepoPaths) -> list[str]:
    """Which per-machine paths a repo's .gitignore does not yet carry."""
    gi = paths.root / ".gitignore"
    try:
        have = set(gi.read_text(encoding="utf-8").splitlines())
    except OSError:
        have = set()
    return [line for line in LOCAL_STATE_IGNORES if line not in have]


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
        elif act == "ensure_modules_current":
            # Same D-042 TIER-1 rationale as the gitignore action below: without
            # this, a newly-added doc module reaches zero existing installs and
            # the shipped stanza/skills dangle. Additive only — create_if_absent
            # never touches an existing doc's bytes (INVARIANT-03).
            from . import assets
            for name in _missing_manifest_modules(config):
                tmpl = assets.doc_template(name)
                if tmpl is None:  # pragma: no cover - filtered upstream
                    continue
                target = paths.doc(name)
                writer.refuse_if_symlink(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                writer.create_if_absent(target, tmpl)
                config.modules.append(name)
            rewrite_config = True
        elif act == "ensure_gitignore_current":
            # D-067 as a D-042 TIER-1 action. Without this the whole policy fix
            # reaches zero existing installs — and every install in the world
            # already ran `init`. Purely additive: lines are appended, never
            # removed, and no docs/ file is touched.
            from .scaffold.init import _ensure_gitignore
            gi = paths.root / ".gitignore"
            for line in _missing_local_state_ignores(paths):
                _ensure_gitignore(gi, line)
        elif act == "refresh_procedure_doc":
            writer.refuse_if_symlink(paths.procedure_file)
            paths.procedure_file.write_text(assets.procedure_text(), encoding="utf-8")
        applied.append(act)
    if rewrite_config:
        # Write-site defense for H-30: even a confused caller cannot move the
        # stamp downward through this path.
        if not _stamp_would_regress(config.procedure_version or ""):
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
