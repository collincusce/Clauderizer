"""``clauderize uninstall`` — reverse init's footprint, keep the memory.

Init writes WIRING (per-host MCP registrations, the Claude Code ``.mcp.json``
key + ``.claude/settings.json`` hooks + hook wrapper, the marker stanzas in
``CLAUDE.md``/``AGENTS.md`` and native rule files, the skills, and the disposable
``.clauderizer/`` dir). Uninstall removes exactly that — and nothing else: the
durable memory under ``docs/`` survives (recoverable with a fresh ``init``), and
every server, hook, and config key Clauderizer did not author is left untouched.

``--host <name>`` scopes to one host's per-host footprint (its MCP registration,
native floor block, and guides). With no host, the FULL footprint is removed.

Non-destructive by construction: each removal strips only the ``clauderizer``
key / marker block / owned file, never the user's surrounding content (the same
key-scoped discipline as the emitters, D-031).
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .. import hosts, hosttargets
from ..markdown import writer
from ..paths import resolve


@dataclass
class UninstallReport:
    host: str | None = None
    removed: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)

    def note(self, what: str | Path) -> None:
        self.removed.append(str(what))


def _remove_mcp_key(mcp_json: Path) -> bool:
    """Drop only the ``clauderizer`` server from ``.mcp.json``; preserve the rest.
    Delete the file only when it held nothing but our (now-empty) registration."""
    if not mcp_json.exists():
        return False
    try:
        data = json.loads(mcp_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or "clauderizer" not in servers:
        return False
    del servers["clauderizer"]
    if not servers and set(data) == {"mcpServers"}:
        mcp_json.unlink()
        return True
    mcp_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _remove_hooks(settings_json: Path) -> bool:
    """Strip every clauderizer hook (any event) from ``.claude/settings.json``,
    leaving foreign hooks and unrelated keys intact. Uses the shared matcher
    (``hosts.is_hook_command``) so it catches direct wiring AND the D4 wrapper."""
    if not settings_json.exists():
        return False
    try:
        data = json.loads(settings_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    changed = False
    for event in list(hooks):
        new_groups = []
        for group in hooks.get(event, []):
            original = group.get("hooks", [])
            kept = [h for h in original
                    if not hosts.is_hook_command(h.get("command", ""))]
            if len(kept) != len(original):
                changed = True
            if kept:
                new_groups.append({**group, "hooks": kept})
            elif not original:
                new_groups.append(group)  # preserve unrelated empty groups verbatim
        if new_groups:
            hooks[event] = new_groups
        else:
            del hooks[event]
            changed = True
    if not changed:
        return False
    if not hooks:
        del data["hooks"]
    if not data:
        settings_json.unlink()
        return True
    settings_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _remove_gitignore_line(gitignore: Path, line: str) -> bool:
    """Remove exactly the line init added, preserving every other entry. Delete
    the file only if it becomes empty."""
    if not gitignore.exists():
        return False
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    if line not in lines:
        return False
    kept = [ln for ln in lines if ln != line]
    if not any(ln.strip() for ln in kept):
        gitignore.unlink()
        return True
    writer.refuse_if_symlink(gitignore)
    gitignore.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return True


def _rmdir_if_empty(path: Path) -> None:
    """Remove a directory only if it is empty (cleans up dirs init created but
    that hold no foreign content)."""
    try:
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    except OSError:
        pass


def _uninstall_host(root: Path, host: str, report: UninstallReport) -> None:
    """The per-host footprint: MCP registration, native floor block, guides."""
    if hosttargets.remove_mcp(host, root):
        report.note(f"{host} MCP registration ({hosttargets.HOST_EMITTERS[host].config_path})")
    if host == "grok" and hosttargets.remove_grok_hooks(root):
        report.note(hosttargets.GROK_HOOKS_REL)
    rel = hosttargets.NATIVE_INSTRUCTIONS.get(host)
    if rel and writer.remove_marker_block(root / rel, "clauderizer"):
        report.note(f"{rel} floor block")
    for name in (f"{host}-hook-setup.md", f"{host}-mcp-setup.md"):
        p = root / ".clauderizer" / name
        if p.exists():
            p.unlink()
            report.note(f".clauderizer/{name}")


def uninstall(root: Path, *, host: str | None = None) -> UninstallReport:
    """Remove Clauderizer's wiring footprint. ``host`` scopes to one host;
    otherwise the full footprint is removed. ``docs/`` is always preserved."""
    root = root.resolve()
    report = UninstallReport(host=host)

    if host is not None:
        hosttargets.parse_host_target(host)  # friendly error on an unknown host
        if host == hosttargets.CLAUDE_CODE:
            if _remove_mcp_key(root / ".mcp.json"):
                report.note(".mcp.json clauderizer key")
            if _remove_hooks(root / ".claude" / "settings.json"):
                report.note(".claude/settings.json clauderizer hooks")
            for wrapper in ("hook.sh", "hook.cmd"):  # D4 wrapper goes with the hook
                p = root / ".clauderizer" / wrapper
                if p.exists():
                    p.unlink()
                    report.note(f".clauderizer/{wrapper}")
        else:
            _uninstall_host(root, host, report)
        report.kept.append("docs/ and .clauderizer/ config preserved (host-scoped uninstall)")
        return report

    # --- full footprint ---------------------------------------------------------
    paths = resolve(root)

    # 1. Claude Code wiring
    if _remove_mcp_key(paths.mcp_json):
        report.note(".mcp.json clauderizer key")
    if _remove_hooks(root / ".claude" / "settings.json"):
        report.note(".claude/settings.json clauderizer hooks")

    # 2. every per-host MCP registration + native instruction floor block
    for host_id in hosttargets.HOST_EMITTERS:
        if hosttargets.remove_mcp(host_id, root):
            report.note(f"{host_id} MCP registration")
    if hosttargets.remove_grok_hooks(root):
        report.note(hosttargets.GROK_HOOKS_REL)
    for host_id, rel in hosttargets.NATIVE_INSTRUCTIONS.items():
        if writer.remove_marker_block(root / rel, "clauderizer"):
            report.note(f"{rel} floor block")

    # 3. marker stanzas in CLAUDE.md + AGENTS.md (preserve the user's own prose)
    for md in (paths.claude_md, paths.agents_md):
        if writer.remove_marker_block(md, "clauderizer"):
            report.note(f"{md.name} stanza")

    # 4. skills installed by init (only clauderizer-* dirs). A planted SYMLINK is
    # unlinked (never followed — shutil.rmtree refuses a symlink and would otherwise
    # abort the whole uninstall mid-footprint); each removal is isolated so one
    # hostile entry can't strand the rest (security review LOW).
    skills_dir = root / ".claude" / "skills"
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            if not d.name.startswith("clauderizer-"):
                continue
            try:
                if d.is_symlink():
                    d.unlink()                 # remove the link, never its target
                elif d.is_dir():
                    shutil.rmtree(d)
                else:
                    continue
                report.note(f".claude/skills/{d.name}")
            except OSError:
                continue                       # don't let one bad entry abort uninstall
        _rmdir_if_empty(skills_dir)
        _rmdir_if_empty(root / ".claude")

    # 5. the disposable .clauderizer dir (config + cache + wrapper + guides). If it
    # is a symlink, unlink it rather than rmtree-following it outside the repo.
    if paths.clauderizer_dir.is_symlink():
        paths.clauderizer_dir.unlink()
        report.note(".clauderizer/ (symlink)")
    elif paths.clauderizer_dir.exists():
        shutil.rmtree(paths.clauderizer_dir, ignore_errors=True)
        report.note(".clauderizer/")

    # 6. the one gitignore line init added
    if _remove_gitignore_line(root / ".gitignore", ".clauderizer/index.json"):
        report.note(".gitignore entry")

    report.kept.append("docs/ (durable memory preserved — re-run `clauderize init` to restore wiring)")
    return report
