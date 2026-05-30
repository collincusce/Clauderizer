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
    def from_file(cls, path: Path) -> "Entity | None":
        try:
            return cls.from_text(path.read_text(encoding="utf-8"), path)
        except (OSError, UnicodeDecodeError):
            return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "version": self.version,
            "status": self.status,
            "depends_on": [str(p) for p in self.depends_on],
            "path": str(self.path),
        }


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
    """
    pat = re.compile(rf"\b{re.escape(prefix)}{re.escape(sep)}(\d+)\b")
    nums = [int(m.group(1)) for m in pat.finditer(text)]
    nxt = (max(nums) + 1) if nums else 1
    return f"{prefix}{sep}{nxt:0{width}d}" if width else f"{prefix}{sep}{nxt}"
