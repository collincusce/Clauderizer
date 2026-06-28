"""Gameplan KINDS — the vocabulary + template + (Phase 3) preflight skin over the
one engine (concurrent-multi-axis-gameplans D1).

A *kind* is the second data-driven axis, orthogonal to the language ``profile``
(profiles/*.toml). It is pure data: a ``kinds/<name>.toml`` file, never engine
code, so adding a kind (a campaign, a research log, a release train) is a new toml
— mirroring how adding a language is a new profile.

The lexicon is **display-only** (D3): it relabels what the agent/user SEE in
digests, handoffs, and op summaries (phase->stage, output->asset, ...). It never
renames on-disk section headings or op names, so every parser and test is
untouched. The DAG, the data model, and the writes are identical across kinds.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_KINDS_DIR = Path(__file__).parent

# The canonical terms a kind may relabel. The engine always uses the canonical
# word internally; ``Kind.label`` maps it to the kind's word for display only.
LEXICON_TERMS = ("phase", "decision", "output", "preflight", "gameplan", "lesson")


@dataclass
class Kind:
    name: str
    lexicon: dict[str, str] = field(default_factory=dict)
    first_phase: str = "Bootstrap"
    # The kind's default preflight check list. Empty = "defer to config" (driven
    # keeps the size-manifest list). Wired into preflight in Phase 3.
    preflight_checks: list[str] = field(default_factory=list)

    def label(self, term: str) -> str:
        """Display label for a canonical term — identity when this kind does not
        relabel it (so ``driven`` is a pure pass-through)."""
        return self.lexicon.get(term, term)

    @classmethod
    def from_toml(cls, path: Path) -> "Kind":
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
        return cls(
            name=str(raw.get("name", path.stem)),
            lexicon={k: str(v) for k, v in raw.get("lexicon", {}).items()},
            first_phase=str(raw.get("template", {}).get("first_phase", "Bootstrap")),
            preflight_checks=list(raw.get("preflight", {}).get("checks", [])),
        )


def load_all(extra_dir: Path | None = None) -> dict[str, Kind]:
    """Every kind: the packaged ``kinds/*.toml`` plus an optional per-repo overlay
    dir (``.clauderizer/kinds/``). An overlay file with a packaged name OVERRIDES
    it; a new name ADDS a custom kind. A malformed overlay file is skipped, never
    fatal (mirrors profiles.load_for_repo)."""
    out: dict[str, Kind] = {}
    for p in sorted(_KINDS_DIR.glob("*.toml")):
        k = Kind.from_toml(p)
        out[k.name] = k
    if extra_dir and extra_dir.exists():
        for p in sorted(extra_dir.glob("*.toml")):
            try:
                k = Kind.from_toml(p)
            except (OSError, tomllib.TOMLDecodeError):
                continue
            out[k.name] = k
    return out


def is_known(name: str, extra_dir: Path | None = None) -> bool:
    return name in load_all(extra_dir)


def resolve(name: str, extra_dir: Path | None = None) -> Kind:
    """The Kind for ``name`` (packaged or overlaid), or a synthetic identity Kind
    for an unknown name — so display relabeling on a legacy/unknown kind never
    crashes; it simply passes terms through unchanged."""
    return load_all(extra_dir).get(name) or Kind(name=name)
