"""``clauderize init`` — drop Clauderizer into a repo.

Every step is idempotent: re-running ``init`` fills gaps and refreshes
engine-owned files, but never clobbers user content. The second run on an
unchanged repo produces zero diffs (a tested invariant).
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .. import assets
from ..config import Config, merge_missing
from ..graph import index
from ..markdown import writer
from ..paths import RepoPaths, resolve
from ..profiles import detect

# Zero-install fallback when nothing is on PATH. uvx resolves the package on
# demand. Overridable with --run-cmd "pipx run clauderizer".
DEFAULT_RUN = ["uvx", "--from", "clauderizer"]


def _resolve_invocation(run_cmd: list[str] | None) -> tuple[list[str], list[str]]:
    """Resolve how this machine should launch the MCP server and the hook.

    Returns ``(mcp_argv, hook_argv)`` as full command lists. When the user passes
    an explicit ``--run-cmd`` prefix, the entry-point name is appended to it.
    Otherwise we prefer the installed console scripts (venv/pipx — the common
    Windows→WSL / venv path that ``uvx``-only wiring used to break), falling back
    to ``uvx --from clauderizer`` only when nothing is on PATH.
    """
    if run_cmd:
        return [*run_cmd, "clauderizer-mcp"], [*run_cmd, "clauderizer-hook"]
    # Prefer the console scripts that sit next to the *running* interpreter — the
    # most reliable hit for a venv/pipx install, even when that bin dir isn't on
    # PATH (the Windows→WSL / unactivated-venv case shutil.which misses). Fall back
    # to PATH lookup, then to zero-install uvx.
    bindir = Path(sys.executable).parent
    mcp = bindir / "clauderizer-mcp"
    hook = bindir / "clauderizer-hook"
    if mcp.exists() and hook.exists():
        return [str(mcp)], [str(hook)]
    which_mcp = shutil.which("clauderizer-mcp")
    which_hook = shutil.which("clauderizer-hook")
    if which_mcp and which_hook:
        return [which_mcp], [which_hook]
    return [*DEFAULT_RUN, "clauderizer-mcp"], [*DEFAULT_RUN, "clauderizer-hook"]


@dataclass
class InitReport:
    repo: str
    host_profile: str = ""
    size: str = ""
    actions: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)

    def note(self, action: str, path: Path | str, changed: bool) -> None:
        verb = "wrote" if changed else "kept"
        self.actions.append(f"{verb} {path}")
        if changed:
            self.changed.append(str(path))


# A "docs"/"audit" workflow accumulates deliverables across phases, so a dirty
# tree and a missing host test runner are normal — these checks become advisory
# (still shown, never fatal) instead of crying wolf on every resume.
WORKFLOW_ADVISORY = {
    "code": [],
    "docs": ["clean_tree", "branch_base", "branch_creation"],
    "audit": ["clean_tree", "branch_base", "branch_creation", "tests"],
}


def init(
    root: Path,
    *,
    size: str = "standard",
    profile: str = "auto",
    gameplan: str | None = None,
    run_cmd: list[str] | None = None,
    workflow: str = "code",
) -> InitReport:
    root = root.resolve()
    paths = resolve(root)
    report = InitReport(repo=str(root))
    mcp_cmd, hook_cmd = _resolve_invocation(run_cmd)

    # 1–2. detect host language
    if profile == "auto":
        prof, _alts = detect.detect(root)
    else:
        prof = detect.load(profile)
    report.host_profile = prof.name

    # 3. size -> default config
    defaults = Config.for_size(size, host_profile=prof.name)
    defaults.preflight_advisory = list(WORKFLOW_ADVISORY.get(workflow, []))
    report.size = size

    # 4. config.toml (merge missing on re-run)
    if paths.config_file.exists():
        existing = Config.load(paths.config_file)
        config = merge_missing(existing, defaults)
    else:
        config = defaults
    changed = writer.create_if_absent(paths.config_file, config.to_toml()) or _rewrite_if_diff(
        paths.config_file, config.to_toml()
    )
    report.note("config", paths.config_file, changed)

    # 5. profile.lock.toml — write once, then PRESERVE. It's the project's editable
    # per-project command override (read back by detect.load_for_repo); regenerating
    # it on every run would clobber those edits. Delete it to re-derive from a profile.
    changed = writer.create_if_absent(paths.profile_lock, prof.to_lock_toml())
    report.note("profile.lock", paths.profile_lock, changed)

    # 6. scaffold docs (enabled modules only; never clobber)
    paths.procedure_file.parent.mkdir(parents=True, exist_ok=True)
    changed = writer.create_if_absent(paths.procedure_file, assets.procedure_text())
    report.note("procedure", paths.procedure_file, changed)
    for module in config.modules:
        tmpl = assets.doc_template(module)
        if tmpl is None:
            continue
        path = paths.doc(module)
        changed = writer.create_if_absent(path, tmpl)
        report.note(f"doc:{module}", path, changed)

    # 7. optional first gameplan
    if gameplan:
        from .. import mutations

        r = mutations.create_gameplan(paths, gameplan)
        config.active_gameplan = r["gameplan_id"]
        _rewrite_if_diff(paths.config_file, config.to_toml())
        report.note("gameplan", r["dir"], bool(r["files_changed"]))

    # 8. CLAUDE.md stanza (marker block; preserves the rest)
    changed = writer.upsert_marker_block(
        paths.claude_md, "clauderizer", assets.template_text("claude_stanza.md")
    )
    report.note("CLAUDE.md", paths.claude_md, changed)

    # 9. install skills (engine-owned: refresh)
    for skill_dir in assets.skill_dirs():
        dest_dir = root / ".claude" / "skills" / skill_dir.name
        for src in skill_dir.iterdir():
            if src.is_file():
                changed = _rewrite_if_diff(dest_dir / src.name, src.read_text(encoding="utf-8"))
                report.note(f"skill:{skill_dir.name}", dest_dir / src.name, changed)

    # 10. register MCP server (key-scoped merge)
    changed = _register_mcp(paths.mcp_json, mcp_cmd)
    report.note(".mcp.json", paths.mcp_json, changed)

    # 11. SessionStart hook (merge into .claude/settings.json)
    changed = _register_hook(root / ".claude" / "settings.json", hook_cmd)
    report.note("hook", root / ".claude" / "settings.json", changed)

    # 12. gitignore the disposable cache; reindex
    changed = _ensure_gitignore(root / ".gitignore", ".clauderizer/index.json")
    report.note(".gitignore", root / ".gitignore", changed)
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)

    return report


# --- helpers ------------------------------------------------------------------


def _rewrite_if_diff(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _register_mcp(mcp_json: Path, mcp_cmd: list[str]) -> bool:
    data = {}
    if mcp_json.exists():
        try:
            data = json.loads(mcp_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    servers = data.setdefault("mcpServers", {})
    entry = {"command": mcp_cmd[0], "args": list(mcp_cmd[1:])}
    if servers.get("clauderizer") == entry:
        return False
    servers["clauderizer"] = entry
    mcp_json.parent.mkdir(parents=True, exist_ok=True)
    mcp_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _register_hook(settings_json: Path, hook_argv: list[str]) -> bool:
    data = {}
    if settings_json.exists():
        try:
            data = json.loads(settings_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    hook_cmd = " ".join(hook_argv)
    hooks = data.setdefault("hooks", {})
    sessionstart = hooks.get("SessionStart", [])

    # Drop ANY existing clauderizer hook entry (matched by the entry-point name),
    # not just an exact-string match. This makes re-running init with a changed
    # invocation (e.g. uvx -> venv path) REPLACE the hook instead of appending a
    # duplicate. Non-clauderizer hooks are preserved untouched.
    cleaned: list[dict] = []
    for group in sessionstart:
        kept = [h for h in group.get("hooks", []) if "clauderizer-hook" not in h.get("command", "")]
        if kept:
            cleaned.append({**group, "hooks": kept})
        elif not group.get("hooks"):
            cleaned.append(group)  # preserve unrelated empty groups verbatim
    cleaned.append({"hooks": [{"type": "command", "command": hook_cmd}]})
    hooks["SessionStart"] = cleaned

    new_text = json.dumps(data, indent=2) + "\n"
    if settings_json.exists() and settings_json.read_text(encoding="utf-8") == new_text:
        return False
    settings_json.parent.mkdir(parents=True, exist_ok=True)
    settings_json.write_text(new_text, encoding="utf-8")
    return True


def _ensure_gitignore(gitignore: Path, line: str) -> bool:
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if line in existing.splitlines():
        return False
    new = existing.rstrip("\n") + ("\n" if existing else "") + line + "\n"
    gitignore.write_text(new, encoding="utf-8")
    return True
