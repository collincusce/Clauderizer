"""Resolve the repo root and all the well-known paths from there.

A "clauderized" repo is any directory containing ``.clauderizer/config.toml``.
For ``init`` on a fresh repo we fall back to the git root, then the cwd.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import ownership


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
    #: Root for ENGINE-owned docs (D-080). ``None`` is the identity default —
    #: engine docs resolve alongside project docs, exactly as before ownership
    #: existed. Set to ``docs/clauderizer`` once a repo is on the split layout.
    engine_docs: Path | None = None

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
    def refusals_file(self) -> Path:
        """Append-only refusal journal (D-070 P1): writes=True ops returning
        ok:False, journaled at the ops REGISTRY seam. Gitignored per-machine
        evidence; read by cz_mine_failures / cz_corpus_health (O-03/D-069)."""
        return self.clauderizer_dir / "refusals.jsonl"

    @property
    def seen_file(self) -> Path:
        """Append-only seen-vs-open engagement receipts (D-073) — per-machine,
        gitignored, disposable labeling state; see ``receipts.py``. The sole
        sanctioned write on a read-declared op (lock-free O_APPEND)."""
        return self.clauderizer_dir / "seen.local.jsonl"

    @property
    def dreams_file(self) -> Path:
        """Append-only dream journal (experiential notes, D-058); see
        ``dreams.py``. Local-only like telemetry.jsonl — gitignored, written
        only by the blessed write-locked op, never a hook."""
        return self.clauderizer_dir / "dreams.jsonl"

    @property
    def procedure_file(self) -> Path:
        return self.gameplans / "GAMEPLAN-PROCEDURE.md"

    @property
    def features_dir(self) -> Path:
        # Tracked entity docs with frontmatter — engine corpus, so they travel
        # with it. Identity default keeps them under docs/ on the legacy layout.
        return self.engine_docs_root / "features"

    @property
    def subsystems_dir(self) -> Path:
        return self.engine_docs_root / "subsystems"

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
        """The generated Kimi Code CLI setup guide (D-049): MCP is auto-written to
        .kimi-code/mcp.json; this guide carries the guide-only pieces — the
        [[hooks]] snippet the user merges into ~/.kimi-code/config.toml and how to
        expose skills (Kimi Code CLI does not read .claude/skills). init never
        edits the global ~/.kimi-code/config.toml itself."""
        return self.clauderizer_dir / "kimi-setup.md"

    @property
    def mcp_json(self) -> Path:
        return self.root / ".mcp.json"

    def gameplan_dir(self, gameplan_id: str) -> Path:
        return self.gameplans / gameplan_id

    @property
    def engine_docs_root(self) -> Path:
        """Where ENGINE-owned docs live (D-080).

        **The identity default is the project docs directory** — with
        ``engine_docs`` unset every path resolves exactly where it resolved
        before ownership existed, so introducing the concept moves nothing and
        changes nothing until a repo opts into the split layout (L-41).
        """
        return self.engine_docs if self.engine_docs is not None else self.docs

    def doc(self, name: str) -> Path:
        """A named living doc, e.g. ``doc('DECISIONS')`` -> docs/DECISIONS.md.

        Routed by OWNER: engine-owned docs resolve under ``engine_docs_root``,
        everything else under the project's ``docs``. On the legacy layout the
        two roots are the same directory, so this is a no-op.
        """
        if not name.endswith(".md"):
            name += ".md"
        root = (self.engine_docs_root
                if ownership.is_engine_owned(name) else self.docs)
        return root / name


def resolve(root: Path, docs_rel: str = "docs", gameplans_rel: str = "docs/gameplans",
            layout: str = ownership.LAYOUT_LEGACY) -> RepoPaths:
    """Resolve a repo's paths.

    ``layout`` defaults to ``legacy``, which leaves ``engine_docs`` unset and so
    resolves every doc exactly where it resolved before D-080 (L-41's identity
    default). ``split`` puts engine-owned docs under ``docs/clauderizer/``.
    """
    root = root.resolve()
    docs = root / docs_rel
    return RepoPaths(
        root=root,
        docs=docs,
        gameplans=root / gameplans_rel,
        engine_docs=(docs / ownership.ENGINE_NAMESPACE
                     if layout == ownership.LAYOUT_SPLIT else None),
    )


def resolve_for_repo(root: Path) -> RepoPaths:
    """``resolve`` honouring the repo's own recorded paths and docs layout.

    The single seam every entry point uses, so a migrated repo resolves its
    engine memory in one place instead of five. ``.clauderizer/config.toml`` sits
    outside the docs tree, so it is readable before the layout is known; an
    unreadable or absent config falls back to the legacy identity, which is
    exactly the pre-D-080 behaviour.
    """
    from .config import Config

    base = resolve(root)
    if not base.config_file.exists():
        return base
    try:
        cfg = Config.load(base.config_file)
    except Exception:
        return base
    return resolve(root, cfg.docs, cfg.gameplans,
                   layout=cfg.docs_layout or ownership.LAYOUT_LEGACY)
