"""Phase 1 experiment: measure prefix-stability of the digest and handoff.

Proxy for provider KV-cache prefix hits: the longest common LEADING substring
between two payloads that differ only in volatile state. A bigger stable prefix
means more of the payload can ride the provider's cached-prefix discount.

Run: .venv/bin/python docs/gameplans/2026-06-19-headroom-borrowed-ideas/_experiments/measure_prefix.py
"""
from clauderizer.rituals import status_bundle, handoff
from clauderizer.ops import repo_ctx


def cp(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


TOOLS = [
    "cz_status", "cz_next_phase_context", "cz_graph_query", "cz_preflight",
    "cz_cascade", "cz_resolve_cascade", "cz_write_handoff", "cz_upsert_entity",
    "cz_transition_status", "cz_add_decision", "cz_add_invariant", "cz_add_finding",
    "cz_resolve_finding", "cz_add_lesson", "cz_obsolete_lesson", "cz_consolidate_lessons",
    "cz_promote_lesson", "cz_add_correction", "cz_add_output", "cz_add_phase_summary",
    "cz_create_gameplan", "cz_add_phase", "cz_transition_phase", "cz_add_amendment",
    "cz_add_open_item", "cz_resolve_open_item", "cz_set_exit_criteria",
    "cz_check_exit_criterion", "cz_analyze", "cz_critique",
]

base = dict(ok=True, size="standard", host_profile="python",
            active_gameplan="2026-06-19-headroom-borrowed-ideas",
            blockers=[], drift=[], engine_stale=False)

# Two "sessions" that differ ONLY in volatile state.
s1 = {**base,
      "summary": 'Gameplan 2026-06-19-headroom-borrowed-ideas: phase 1/5 IN PROGRESS — "Idea 1 — Prefix-stability".',
      "baseline_tests": "305",
      "memory": {"active_lessons": 1, "project_lessons": 16, "handoff_est_tokens": 1200, "warning": None},
      "pending_cascades": [], "open_items": ["O-01", "O-02", "O-03"],
      "next_action": "cz_preflight, then execute the phase tasks."}
s2 = {**base,
      "summary": 'Gameplan 2026-06-19-headroom-borrowed-ideas: phase 3/5 IN PROGRESS — "Idea 3 — Failure-miner".',
      "baseline_tests": "312",
      "memory": {"active_lessons": 4, "project_lessons": 17, "handoff_est_tokens": 1850,
                 "warning": "4 active lessons (> 12)"},
      "pending_cascades": ["2026-06-19-subsys.rituals.md"], "open_items": ["O-02"],
      "next_action": "cz_preflight, then execute the phase tasks."}

d1 = status_bundle.render_digest(s1, TOOLS)
d2 = status_bundle.render_digest(s2, TOOLS)
c = cp(d1, d2)
print("=== DIGEST (current order) ===")
print(f"len d1={len(d1)}  len d2={len(d2)}  common_prefix={c}  ({100*c/len(d1):.1f}% of d1, ~{c//4} tok)")
print("stable prefix repr:", repr(d1[:c]))
print()


def render_stable_first(b, tools):
    """Same information, stable lines first, volatile last."""
    L = ["[Clauderizer] durable working-memory engine active.",
         f"Profile: {b['size']} / {b['host_profile']}."]
    if tools:
        L.append("Tools: " + ", ".join(tools))
    L.append("Protocol: cz_status refreshes; cz_next_phase_context + cz_preflight begin a phase.")
    L.append("--- current state ---")
    L.append(b["summary"])
    if b.get("baseline_tests"):
        L.append(f"Baseline: {b['baseline_tests']} tests.")
    m = b.get("memory") or {}
    L.append(f"Memory: {m.get('active_lessons')} active lessons, {m.get('project_lessons')} project.")
    pc = b.get("pending_cascades") or []
    L.append(f"Pending cascades: {len(pc)}." + (f" {', '.join(pc)}" if pc else ""))
    oi = b.get("open_items") or []
    if oi:
        L.append(f"Open items: {len(oi)} ({', '.join(oi)}).")
    L.append(f"Next: {b.get('next_action', '')}")
    return "\n".join(L)


r1 = render_stable_first(s1, TOOLS)
r2 = render_stable_first(s2, TOOLS)
c2 = cp(r1, r2)
print("=== DIGEST (stable-first reorder) ===")
print(f"len r1={len(r1)}  len r2={len(r2)}  common_prefix={c2}  ({100*c2/len(r1):.1f}% of r1, ~{c2//4} tok)")
print("stable prefix repr:", repr(r1[:c2]))
print()

# HANDOFF: real assembler, two different phases of THIS gameplan.
paths, config = repo_ctx()
gid = config.active_gameplan
try:
    h1 = handoff.assemble(paths, config, gid, "1", write=False)["handoff_md"]
    h3 = handoff.assemble(paths, config, gid, "3", write=False)["handoff_md"]
    c3 = cp(h1, h3)
    print("=== HANDOFF (phase 1 vs phase 3, current order) ===")
    print(f"len h1={len(h1)}  len h3={len(h3)}  common_prefix={c3}  ({100*c3/len(h1):.1f}% of h1, ~{c3//4} tok)")
    print("first divergence context:", repr(h1[max(0, c3 - 30):c3 + 50]))
except Exception as e:  # noqa: BLE001
    print("handoff measure failed:", type(e).__name__, e)
