"""Phase 4 regression guard (gameplan abstract-index-fast-retrieval): the
AUTO-INJECTED surfaces carry cz_get-addressable POINTERS, never entry bodies (D-013).

Phase 4 ("realize the win in injected surfaces") found the win already banked:
the status digest is counts+pointers only (D-027 trim, ~315 tok), and the handoff
carries invariant/lesson POINTERS plus lessons-in-full (mandated by D-009), with NO
decision/finding bodies injected anywhere — decisions and findings are retrieval-only
via the Phase-2 cz_get (by id). These tests LOCK that property at the shared
injection seam (the L-34 integration point) so a future "enrichment" cannot silently
start injecting full bodies — the exact anti-pattern D-013 (pointer, not body store)
exists to prevent. The realized token win lives in the retrieval path (Phase 3,
48.3%) and the prior focused-injection (-55%), not in re-shaping these surfaces.
"""
from clauderizer import config as C
from clauderizer import mutations as M
from clauderizer import paths as P
from clauderizer.rituals import handoff, status_bundle
from clauderizer.tools_list import TOOL_NAMES

_INVARIANTS_DOC = (
    "## Invariants\n\n"
    "### INVARIANT-90 — cascade advisory write flow\n\n"
    "INV_BODY_MARKER_zzz the full invariant body the pointer must NOT inject.\n"
)


def test_invariant_injection_surfaces_pointer_not_body(temp_repo):
    """The invariant injection surface reads INVARIANTS.md but emits only id+title —
    a cz_get-addressable pointer (the id is the handle, the title is the abstract) —
    never the body. This is the surface that COULD inject a body and deliberately
    does not (D-013)."""
    paths = P.resolve(temp_repo)
    paths.doc("INVARIANTS").write_text(_INVARIANTS_DOC, encoding="utf-8")
    res = handoff.relevant_invariant_pointer(paths, "cascade advisory write flow", k=2)
    assert res is not None
    md, _shown, _total = res
    assert "INVARIANT-90" in md                    # the id (the cz_get handle) is surfaced
    assert "cascade advisory write flow" in md     # the title (the abstract) is surfaced
    assert "INV_BODY_MARKER_zzz" not in md         # the BODY is NOT injected (D-013)


def test_injected_surfaces_carry_no_decision_or_finding_bodies(temp_repo):
    """End-to-end at the shared seam: neither the assembled handoff nor the hook
    digest injects a decision or finding BODY. Those are fetched on demand via
    cz_get (Phase 2/3), never auto-injected (D-013) — guard against a future change
    that "enriches" an injected surface with full bodies."""
    paths = P.resolve(temp_repo)
    config = C.Config.load(paths.config_file)
    gid = config.active_gameplan
    M.add_decision(paths, title="adopt a widget pipeline",
                   context="DECISION_BODY_MARKER_aaa durable widget throughput rationale",
                   decision="build it", consequences="more widgets")
    M.add_finding(paths, title="a concurrency race", severity="high",
                  impact="FINDING_BODY_MARKER_bbb data loss under contention")
    # the auto-injected handoff (cz_next_phase_context / cz_write_handoff)
    hmd = handoff.assemble(paths, config, gid, "1", write=False)["handoff_md"]
    assert "Phase 1 Handoff" in hmd                 # assemble actually ran
    assert "DECISION_BODY_MARKER_aaa" not in hmd    # no decision body injected
    assert "FINDING_BODY_MARKER_bbb" not in hmd     # no finding body injected
    # the hook-injected SessionStart/UserPromptSubmit digest
    digest = status_bundle.render_digest(
        status_bundle.compute(paths, config), tools=TOOL_NAMES)
    assert "DECISION_BODY_MARKER_aaa" not in digest
    assert "FINDING_BODY_MARKER_bbb" not in digest
