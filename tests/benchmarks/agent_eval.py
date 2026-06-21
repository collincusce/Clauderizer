"""Agent-eval scaffolding: the focused-vs-full ablation (D: hybrid gain-gate).

The deterministic metrics gate CI; this layer confirms the *behavioral* gain for
features whose benefit is "does the agent answer better", which a deterministic
proxy cannot fully capture. It cannot run in CI (no model), so it is a documented,
seeded procedure the orchestrator drives by spawning paired sub-agents.

Procedure (run during a feature phase):
  1. Pick a Probe (or a set) from :mod:`corpora`.
  2. Build two contexts for the SAME probe query:
       - focused: only the ranker-selected top-k memory (the feature ON)
       - full:    the whole memory dumped (the feature OFF / status quo)
  3. Spawn two sub-agents with identical instructions, one per context, asking the
     probe query. Temperature pinned low; vary nothing but the context arm.
  4. Score each answer with :func:`score_answer` against the probe's answer key.
  5. The behavioral gain = accuracy(focused) - accuracy(full). The research
     prediction (LongMemEval / Context Rot) is that focused >= full; a feature
     that injects MORE context must show it does not regress this.

This module builds the contexts and scores answers deterministically; the model
calls themselves are made by the orchestrator via the Agent tool.
"""
from __future__ import annotations

from . import harness


def render_entries(entries: list[dict]) -> str:
    """Render entries as the memory block an agent would receive."""
    return "\n".join(f"- {e['id']}: {e['title']} — {e.get('body', '')}".rstrip(" —")
                     for e in entries)


def build_full_context(entries: list[dict]) -> str:
    """The status-quo arm: dump every memory entry (the 'inject everything' path)."""
    return render_entries(entries)


def build_focused_context(query: str, entries: list[dict], k: int = 5) -> str:
    """The feature arm: only the ranker-selected top-k entries, front-loaded."""
    top_ids = set(harness.rank_ids(query, entries, k))
    return render_entries([e for e in entries if e["id"] in top_ids])


def make_prompt(context: str, query: str) -> str:
    """The identical instruction given to each sub-agent; only ``context`` varies."""
    return (
        "You are answering from project memory ONLY. If the answer is not in the "
        "memory below, reply exactly 'NOT IN MEMORY'.\n\n"
        f"--- project memory ---\n{context}\n--- end memory ---\n\n"
        f"Question: {query}\n"
        "Answer with the single most relevant memory id, or 'NOT IN MEMORY'."
    )


def score_answer(answer: str, probe) -> bool:
    """Deterministic scoring against the probe's answer key.

    Abstention probe (no relevant ids): correct iff the agent declined.
    Otherwise: correct iff the answer names a relevant id and no stale id.
    """
    text = (answer or "").strip().lower()
    if not probe.relevant_ids:
        return "not in memory" in text
    names_relevant = any(rid.lower() in text for rid in probe.relevant_ids)
    names_stale = any(sid.lower() in text for sid in probe.stale_ids)
    return names_relevant and not names_stale


def build_arms(probe, entries: list[dict], k: int = 5) -> dict:
    """Return the two ready-to-send prompts for one probe (focused vs full)."""
    return {
        "focused": make_prompt(build_focused_context(probe.query, entries, k), probe.query),
        "full": make_prompt(build_full_context(entries), probe.query),
        "probe": probe,
    }
