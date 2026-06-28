"""Guard: there is exactly ONE token-splitter in the engine (D-041).

All lexical-overlap / similarity computations — relevance ranking
(analyze.rank_relevant), the write-time near-duplicate-lesson advisory
(analyze.near_duplicate_lessons), the abstract index's per-entry token_set,
and the corpus-health / curator redundancy metric (telemetry.corpus_health /
curate_proposals) — must tokenize through the single canonical
``analyze._tokens``. The v1.3.0 integrity audit found a second, divergent fork
in ``telemetry._tokens`` (kept stopwords + 3-char noise). These tests stop a
third fork from quietly reappearing: they are the enforcement that makes D-041
machine-checked (and the precondition for promoting it to an invariant)."""

from __future__ import annotations

import re
from pathlib import Path

from clauderizer import analyze, telemetry

_SRC = Path(analyze.__file__).parent
_DEF_TOKENS_RE = re.compile(r"^def _tokens\b", re.M)


def test_exactly_one_token_splitter_definition_in_src():
    """A literal ``def _tokens`` may appear in exactly one module (analyze.py).

    A second module-level definition means a fork has reappeared — fail loudly
    with the offending files so the canonical-tokenizer invariant (D-041) is
    restored rather than silently re-diverging."""
    offenders = []
    for py in sorted(_SRC.rglob("*.py")):
        text = py.read_text(encoding="utf-8")
        if _DEF_TOKENS_RE.search(text):
            offenders.append(py.relative_to(_SRC.parent).as_posix())
    assert offenders == ["clauderizer/analyze.py"], (
        f"expected the canonical _tokens to be defined only in analyze.py; "
        f"found definitions in: {offenders}"
    )


def test_telemetry_tokens_is_the_canonical_tokens():
    """telemetry routes through the canonical tokenizer by import identity —
    not a re-implementation that merely behaves the same today."""
    assert telemetry._tokens is analyze._tokens


def test_redundancy_threshold_is_single_sourced_with_the_write_time_advisory():
    """corpus_health / curate share ONE near-duplicate threshold with the
    write-time advisory (analyze.near_duplicate_lessons), so a lesson pair can't
    be a near-duplicate for cz_add_lesson yet not for cz_corpus_health."""
    assert telemetry._REDUNDANCY_THRESHOLD == analyze._LESSON_DUP_JACCARD
