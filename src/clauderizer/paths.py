"""Resolve the repo root and all the well-known paths from there.

A "clauderized" repo is any directory containing ``.clauderizer/config.toml``.
For ``init`` on a fresh repo we fall back to the git root, then the cwd.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if (d / ".clauderizer" / "config.toml").exists():
            return d
    for d in (start, *start.parents):
        if (d / ".git").exists():
            return d
    return start


@dataclass(frozen=True)
class RepoPaths:
    root: Path
    docs: Path
    gameplans: Path

    @property
    def clauderizer_dir(self) -> Path:
        return self.root / ".clauderizer"

    @property
    def config_file(self) -> Path:
        return self.clauderizer_dir / "config.toml"

    @property
    def index_file(self) -> Path:
        return self.clauderizer_dir / "index.json"

    @property
    def abstract_index_file(self) -> Path:
        """The per-entry abstract index over the append-only corpus — a disposable
        cache (sibling of ``index.json``), rebuilt from markdown on demand
        (INVARIANT-01); see ``graph/abstract_index.py``."""
        return self.clauderizer_dir / "abstract_index.json"

    @property
    def profile_lock(self) -> Path:
        return self.clauderizer_dir / "profile.lock.toml"

    @property
    def kinds_dir(self) -> Path:
        """Per-repo gameplan-kind overlay: ``.clauderizer/kinds/<name>.toml`` files
        that override a packaged kind or add a custom one (kinds.load_all overlay)."""
        return self.clauderizer_dir / "kinds"

    @property
    def write_lock_file(self) -> Path:
        """The advisory inter-process write lock (H-05); see ``locking.py``."""
        return self.clauderizer_dir / "write.lock"

    @property
    def telemetry_file(self) -> Path:
        """Append-only memory telemetry (surfacing + phase outcomes); see
        ``telemetry.py``. Written only by blessed write-locked ops, never a hook."""
        return self.clauderizer_dir / "telemetry.jsonl"

    @property
    def procedure_file(self) -> Path:
        return self.gameplans / "GAMEPLAN-PROCEDURE.md"

    @property
    def features_dir(self) -> Path:
        return self.docs / "features"

    @property
    def subsystems_dir(self) -> Path:
        return self.docs / "subsystems"

    @property
    def claude_md(self) -> Path:
        return self.root / "CLAUDE.md"

    @property
    def agents_md(self) -> Path:
        """The cross-harness instructions file (kimi reads it via KIMI_AGENTS_MD;
        Codex and others honor it too). init injects the same marker-block stanza
        as CLAUDE.md here, so AGENTS.md-aware hosts get Clauderizer too (D2)."""
        return self.root / "AGENTS.md"

    @property
    def kimi_setup(self) -> Path:
        """The generated, non-destructive kimi-code wiring guide (D2): the
        [[hooks]] snippet + MCP guidance the user merges into their own kimi
        config. init never edits the global ~/.kimi/config.toml itself."""
        return self.clauderizer_dir / "kimi-setup.md"

    @property
    def mcp_json(self) -> Path:
        return self.root / ".mcp.json"

    def gameplan_dir(self, gameplan_id: str) -> Path:
        return self.gameplans / gameplan_id

    def doc(self, name: str) -> Path:
        """A named living doc, e.g. ``doc('DECISIONS')`` -> docs/DECISIONS.md."""
        if not name.endswith(".md"):
            name += ".md"
        return self.docs / name


def resolve(root: Path, docs_rel: str = "docs", gameplans_rel: str = "docs/gameplans") -> RepoPaths:
    root = root.resolve()
    return RepoPaths(
        root=root,
        docs=root / docs_rel,
        gameplans=root / gameplans_rel,
    )
