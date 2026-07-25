"""Core data shapes parsed out of the markdown source of truth.

Everything here is derived from files on disk. Nothing here is authoritative;
the markdown is. These dataclasses are the in-memory view used by the graph
index, the rituals, and the MCP tools.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .markdown import frontmatter

# A dependency pin like "subsys.auth@^1.0.0" or just "subsys.auth".
_PIN_RE = re.compile(r"^(?P<id>[^@\s]+)(?:@(?P<constraint>.+))?$")


@dataclass
class Pin:
    target: str
    constraint: str | None = None

    @classmethod
    def parse(cls, raw: str) -> "Pin":
        m = _PIN_RE.match(raw.strip())
        if not m:
            return cls(target=raw.strip())
        return cls(target=m.group("id"), constraint=m.group("constraint"))

    def __str__(self) -> str:
        return f"{self.target}@{self.constraint}" if self.constraint else self.target


@dataclass
class Entity:
    """A frontmatter-tracked node in the long-lived Project DAG."""

    id: str
    type: str
    path: Path
    version: str | None = None
    status: str | None = None
    depends_on: list[Pin] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    @classmethod
    def from_text(cls, text: str, path: Path) -> "Entity | None":
        data, body = frontmatter.parse(text)
        if not data or "id" not in data or "type" not in data:
            return None
        deps = [Pin.parse(str(d)) for d in (data.get("depends_on") or [])]
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            path=path,
            version=_opt_str(data.get("version")),
            status=_opt_str(data.get("status")),
            depends_on=deps,
            raw=data,
            body=body,
        )

    @classmethod
    def from_file(cls, path: Path) -> "Entity | Drop | None":
        """An ``Entity``, a ``Drop``, or ``None``.

        The three-way return is the point (D-018/D-065). ``None`` means "this is
        not an entity doc" — the ordinary case for prose under ``docs/``. A
        ``Drop`` means "this file was TRYING to be a tracked entity and could not
        be indexed", which the bare ``None`` this used to return made
        indistinguishable from the ordinary case: a BOM'd entity doc vanished
        from the graph in silence, and every consumer then reasoned about a DAG
        that was quietly missing a node.
        """
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return Drop(path, "undecodable", f"not valid UTF-8: {exc}")
        except OSError as exc:
            return Drop(path, "unreadable", str(exc))
        entity = cls.from_text(text, path)
        return entity if entity is not None else _classify_drop(text, path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "version": self.version,
            "status": self.status,
            "depends_on": [str(p) for p in self.depends_on],
            # Structured edges (O-16): clients label graph edges with their pin
            # without re-parsing the `target@constraint` string form above.
            "depends_on_pins": [
                {"target": p.target, "constraint": p.constraint}
                for p in self.depends_on
            ],
            "path": str(self.path),
        }


@dataclass(frozen=True)
class Drop:
    """A ``docs/`` file that was trying to be a tracked entity and could not be
    indexed. Carries the path so the report can name it (a count alone is not
    actionable) and a machine-readable ``reason``."""

    path: Path
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"path": str(self.path), "reason": self.reason, "detail": self.detail}

    def describe(self) -> str:
        return f"{self.path}: {self.reason}" + (f" ({self.detail})" if self.detail else "")


#: A byte-order mark ahead of the fence. PowerShell and several Windows editors
#: write UTF-8 BOM by default, and ``has_frontmatter`` anchors on ``---`` at
#: offset zero — so the whole entity silently stops existing (the L-24 class).
_BOM = "﻿"


def _classify_drop(text: str, path: Path) -> "Drop | None":
    """Why an entity-shaped file failed to parse, or ``None`` if it was never
    entity-shaped to begin with.

    Deliberately conservative: a doc with no frontmatter, or with frontmatter
    carrying neither ``id`` nor ``type``, is ordinary prose and reports nothing.
    Only a file that clearly INTENDED to be an entity is a drop, so the count is
    actionable rather than a standing false positive.
    """
    if text.startswith(_BOM) and frontmatter.has_frontmatter(text.lstrip(_BOM)):
        return Drop(path, "bom-before-frontmatter",
                    "a byte-order mark precedes the opening --- fence, so the "
                    "frontmatter is never recognized; re-save as UTF-8 without BOM")
    if frontmatter.has_frontmatter(text):
        block, _ = frontmatter.split(text)
        if block is None:
            return Drop(path, "unterminated-frontmatter",
                        "the opening --- fence is never closed")
        data = frontmatter.parse_block(block)
        has_id, has_type = "id" in data, "type" in data
        if has_id != has_type:
            missing = "type" if has_id else "id"
            return Drop(path, "incomplete-frontmatter", f"missing required '{missing}'")
    return None


def _opt_str(v: Any) -> str | None:
    return None if v is None else str(v)


# --- semver (the subset cascade needs) ---------------------------------------


@dataclass
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, raw: str | None) -> "SemVer | None":
        if not raw:
            return None
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)", str(raw).strip())
        if not m:
            return None
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def constraint_satisfied(version: str | None, constraint: str | None) -> bool | None:
    """Does ``version`` satisfy ``constraint``?

    Supports ``^x.y.z`` (caret: same major), ``~x.y.z`` (tilde: same major+minor),
    and an exact ``x.y.z``. Returns ``None`` when either side is unparseable
    (caller treats unknown as "not a violation").
    """
    if not constraint:
        return True
    v = SemVer.parse(version)
    op = constraint[0]
    base = SemVer.parse(constraint.lstrip("^~"))
    if v is None or base is None:
        return None
    if op == "^":
        return v.major == base.major and (v.major, v.minor, v.patch) >= (
            base.major,
            base.minor,
            base.patch,
        )
    if op == "~":
        return (
            v.major == base.major
            and v.minor == base.minor
            and v.patch >= base.patch
        )
    return (v.major, v.minor, v.patch) == (base.major, base.minor, base.patch)


# --- numbered-entry helpers (D-NNN, INVARIANT-NN, A-NNN, C-NN, H-NN) ----------


def next_numbered_id(text: str, prefix: str, *, sep: str = "-", width: int = 3) -> str:
    """Compute the next id for an append-only numbered series found in ``text``.

    e.g. ``next_numbered_id(doc, "D")`` over a doc containing ``D-001``, ``D-002``
    returns ``D-003``. Padding width matches ``width`` (set ``width=0`` for the
    bare ``D1``/``C2`` gameplan-internal style).

    Only IDs at *entry anchors* count: ``### <ID> — …`` headings and
    ``**<ID>.**`` bold log entries at line start. Mentions inside prose —
    scaffold placeholders ("D1, D2, …") or cross-references to another
    document's IDs — never shift the sequence (C-01 of discipline-seams; the
    engine-structural-robustness gameplan's own decisions skipped D6 because a
    decision's text cited another gameplan's D6).
    """
    core = rf"{re.escape(prefix)}{re.escape(sep)}(\d+)"
    pat = re.compile(rf"^(?:#{{1,6}}\s+{core}\b|\s*\*\*{core}\.\*\*)", re.M)
    nums = [int(m.group(1) or m.group(2)) for m in pat.finditer(text)]
    nxt = (max(nums) + 1) if nums else 1
    return f"{prefix}{sep}{nxt:0{width}d}" if width else f"{prefix}{sep}{nxt}"
