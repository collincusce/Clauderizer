"""Subsystem docs get an executable seam against the module they describe (H-24).

L-62 established the discipline — a doc that enumerates a code-owned surface must
be pinned by a test that diffs it against the source of truth — and it was applied
to the README's tool list and the procedure-version header, never to
`docs/subsystems/*.md`, which are exactly the docs whose *job* is to enumerate a
module's surface. The D-066 write boundary shipped in 1.14.0 with no mention in
`mutations.md` and was found a release later, by accident.

SCOPE, stated honestly rather than implied (see amendment A-001 of this gameplan).
This catches a **whole undocumented public surface** — a module or a public
callable the doc never mentions. It does NOT catch what actually happened to
D-066: `_safe_body` is *private*, and what was missing was a conceptual section.
No mechanical check distinguishes "this doc discusses the right ideas" from "this
doc is stale"; claiming otherwise would be the false green this release exists to
end. The narrower guarantee is real and is what ships.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
def _repo_engine_docs():
    """This repo's ENGINE-owned docs root, honouring its docs layout (D-080).

    Hardcoding `ROOT / "docs"` broke the moment the engine's own repo migrated —
    which is exactly the drift these seam tests exist to catch, so they resolve
    it the way the engine does rather than assuming a layout.
    """
    from clauderizer.paths import resolve_for_repo
    return resolve_for_repo(ROOT).engine_docs_root
SUBSYS_DOCS = _repo_engine_docs() / "subsystems"
SRC = ROOT / "src" / "clauderizer"

#: Doc stem -> module/package under src/. Only for the few where the doc name is
#: not the module name; `test_every_subsystem_doc_maps_to_real_code` fails loudly
#: if a new doc appears without a mapping, so this cannot silently go stale.
ALIASES = {"markdown-core": "markdown", "mcp-server": "mcp_server",
           "session-ledger": "session_ledger", "state-stamp": "state_stamp"}

#: Public callables so generic that a doc naming them proves nothing.
_UNINFORMATIVE = {"main", "run", "load", "parse", "build", "read", "write"}


def _module_path(stem: str) -> Path | None:
    name = ALIASES.get(stem, stem.replace("-", "_"))
    for cand in (SRC / f"{name}.py", SRC / name):
        if cand.exists():
            return cand
    return None


def _public_api(target: Path) -> set[str]:
    """Top-level public callables and classes defined by a module or package."""
    files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
    names: set[str] = set()
    for f in files:
        if f.name == "__init__.py":
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_") and node.name not in _UNINFORMATIVE:
                    names.add(node.name)
    return names


def _doc_stems() -> list[str]:
    return sorted(p.stem for p in SUBSYS_DOCS.glob("*.md"))


# --- the map itself cannot go stale --------------------------------------------

def test_every_subsystem_doc_maps_to_real_code():
    """A new subsystem doc with no module — or a renamed module — fails here
    rather than silently dropping out of coverage below."""
    missing = [s for s in _doc_stems() if _module_path(s) is None]
    assert not missing, f"subsystem docs with no resolvable module: {missing}"


def test_aliases_are_all_used():
    """A stale alias is its own drift."""
    unused = [k for k in ALIASES if k not in _doc_stems()]
    assert not unused, f"ALIASES entries for docs that no longer exist: {unused}"


# --- the seam ------------------------------------------------------------------

BASELINE = Path(__file__).parent / "fixtures" / "subsystem_doc_baseline.json"


def _undocumented(stem: str) -> list[str]:
    api = _public_api(_module_path(stem))
    text = (SUBSYS_DOCS / f"{stem}.md").read_text(encoding="utf-8")
    return sorted(n for n in api if n not in text)


def _baseline() -> dict[str, int]:
    return json.loads(BASELINE.read_text(encoding="utf-8"))["undocumented_per_subsystem"]


def _unmapped_baseline() -> set[str]:
    return set(json.loads(BASELINE.read_text(encoding="utf-8"))["modules_with_no_subsystem_doc"])


def _top_level_modules() -> set[str]:
    return {p.stem if p.suffix == ".py" else p.name for p in SRC.iterdir()
            if (p.suffix == ".py" and not p.name.startswith("_"))
            or (p.is_dir() and not p.name.startswith("_"))}


def _mapped_modules() -> set[str]:
    out = set()
    for stem in _doc_stems():
        m = _module_path(stem)
        if m is not None:
            out.add(m.stem if m.suffix == ".py" else m.name)
    return out


def test_no_new_module_escapes_the_seam():
    """The hole the per-subsystem ratchet alone leaves open.

    Only 8 of ~40 modules sit under a subsystem doc, so the ratchet above
    silently ignores the rest — and both modules written during 1.14.1/1.14.2
    (nesting, engine_identity) landed in that blind spot. A check with a blind
    spot that large is the false green this release exists to end.

    So the UNMAPPED SET is itself ratcheted: it may only shrink. Adding a new
    module now forces a choice — document it under a subsystem, or record it
    here deliberately. What it can no longer be is an accident.
    """
    escaped = _top_level_modules() - _mapped_modules() - _unmapped_baseline()
    assert not escaped, (
        f"new module(s) with no subsystem doc and no recorded exemption: "
        f"{sorted(escaped)}. Document them under docs/subsystems/, or add them "
        f"to modules_with_no_subsystem_doc in {BASELINE.name} with a reason in "
        f"the commit message.")


def test_the_unmapped_set_tightens_when_a_module_gets_documented():
    """Same ratchet discipline: retiring an exemption must lower the baseline,
    or the slack becomes room for the next undocumented module to hide in."""
    stale = _unmapped_baseline() - _top_level_modules()
    covered = _unmapped_baseline() & _mapped_modules()
    assert not stale, f"exempted modules that no longer exist: {sorted(stale)}"
    assert not covered, (
        f"now documented, so remove from the exemption list: {sorted(covered)}")


@pytest.mark.parametrize("stem", sorted(_baseline()))
def test_undocumented_surface_never_grows(stem):
    """A strict RATCHET, not a report.

    An advisory that never fails is how rot happens — it is the same write-only
    shape as a findings register nobody empties. But a fixed target ("80% of
    callables documented") would be an invented number, and inventing one is how
    a check earns its way into the ignore list.

    So: no target, no advice. The number of undocumented public callables per
    subsystem is recorded in fixtures/subsystem_doc_baseline.json, and it may
    only go DOWN. Land a new public callable without documenting it and this
    fails. The existing debt is frozen exactly where it stands, visibly, instead
    of being laundered into a passing check.
    """
    actual, allowed = len(_undocumented(stem)), _baseline()[stem]
    assert actual <= allowed, (
        f"docs/subsystems/{stem}.md now omits {actual} public callables, up from "
        f"{allowed}: {_undocumented(stem)}. Document the new surface, or if this "
        f"is deliberate, raise the baseline WITH a reason in the commit message — "
        f"the point is that growing the debt has to be a decision.")


@pytest.mark.parametrize("stem", sorted(_baseline()))
def test_the_ratchet_tightens_when_docs_improve(stem):
    """The other direction, which is what makes it a ratchet rather than a cap:
    documenting something must lower the baseline, or the slack silently becomes
    room for the next undocumented symbol to hide in."""
    actual, allowed = len(_undocumented(stem)), _baseline()[stem]
    assert actual >= allowed, (
        f"docs/subsystems/{stem}.md improved — it now omits only {actual} "
        f"callables, below the recorded {allowed}. Lower {BASELINE.name} to "
        f"{actual} to lock the gain in.")


def test_the_baseline_covers_exactly_the_checkable_subsystems():
    """A subsystem dropping out of the baseline would silently drop out of the
    ratchet — the gap that lets a whole doc rot unobserved."""
    checkable = {s for s in _doc_stems() if _public_api(_module_path(s))}
    assert set(_baseline()) == checkable, (
        f"baseline drift: {checkable ^ set(_baseline())}")
