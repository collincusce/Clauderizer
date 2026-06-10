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

from .. import assets, hosts
from ..config import Config, merge_missing
from ..graph import index
from ..markdown import writer
from ..paths import RepoPaths, resolve
from ..profiles import detect

# Zero-install fallback when nothing is on PATH. uvx resolves the package on
# demand. Overridable with --run-cmd "pipx run clauderizer".
DEFAULT_RUN = ["uvx", "--from", "clauderizer"]


class WiringRefused(RuntimeError):
    """A composed wiring command failed its spawn test; nothing was written.

    The H-04 regression guard: init must never write a command the session
    host cannot launch (e.g. a multi-word --run-cmd that composes an invalid
    subcommand like ``clauderize clauderizer-mcp``).
    """


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
    # PATH (the Windows→WSL / unactivated-venv case shutil.which misses). On
    # win32 the scripts carry .exe (and live in Scripts/, which IS the
    # interpreter's dir for a venv). Fall back to PATH lookup, then uvx.
    bindir = Path(sys.executable).parent

    def _script(name: str) -> Path | None:
        for candidate in (bindir / f"{name}.exe", bindir / name):
            if candidate.exists():
                return candidate
        return None

    mcp = _script("clauderizer-mcp")
    hook = _script("clauderizer-hook")
    if mcp and hook:
        return [str(mcp)], [str(hook)]
    which_mcp = shutil.which("clauderizer-mcp")
    which_hook = shutil.which("clauderizer-hook")
    if which_mcp and which_hook:
        return [which_mcp], [which_hook]
    # Absolutize uvx when present: hooks and shimmed commands run in non-login
    # shells whose PATH may not include ~/.local/bin (observed live on WSL).
    uvx = shutil.which(DEFAULT_RUN[0]) or DEFAULT_RUN[0]
    run = [uvx, *DEFAULT_RUN[1:]]
    return [*run, "clauderizer-mcp"], [*run, "clauderizer-hook"]


@dataclass
class InitReport:
    repo: str
    host_profile: str = ""
    size: str = ""
    session_host: str = ""
    actions: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

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
    session_host: str | None = None,
    spawn_test: bool = True,
) -> InitReport:
    root = root.resolve()
    paths = resolve(root)
    report = InitReport(repo=str(root))

    # 0. session host of record (D3): explicit flag > what config already
    # records > adoption of the host the existing wiring serves > native.
    existing_config = Config.load(paths.config_file) if paths.config_file.exists() else None
    resolved_host = (
        session_host
        or (existing_config.session_host if existing_config else None)
        or hosts.detect(hosts.read_wiring(paths.mcp_json))
    )
    hosts.parse(resolved_host)  # invalid values fail loudly before anything composes
    report.session_host = resolved_host

    engine_mcp, engine_hook = _resolve_invocation(run_cmd)
    mcp_cmd = hosts.compose(engine_mcp, resolved_host)
    hook_cmd = hosts.compose(engine_hook, resolved_host)

    # 0b. spawn-test every composed command BEFORE any write (H-04 guard):
    # wiring that cannot answer --version must never reach .mcp.json or the
    # hook registration. "Unverifiable" (no interop path to the session host)
    # proceeds with a loud warning naming the command to certify from there.
    if spawn_test:
        for label, argv in (("MCP server", mcp_cmd), ("SessionStart hook", hook_cmd)):
            probe = hosts.spawn_probe(argv)
            if probe.status == "fail":
                raise WiringRefused(
                    f"the composed {label} command failed its spawn test — "
                    f"nothing was written.\n"
                    f"  command: {' '.join(argv)}\n"
                    f"  probe:   {probe.detail}\n"
                    f"  Drop --run-cmd to let init resolve the installed console "
                    f"scripts, or pass\n"
                    f"  --session-host windows-wsl:<distro> for a WSL engine driven "
                    f"from Windows."
                )
            if probe.status == "unverifiable":
                report.warnings.append(f"{label} wiring unverifiable: {probe.detail}")

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

    # 4. config.toml (merge missing on re-run); record the session host of
    # record so every later init/doctor composes and verifies for it.
    config = merge_missing(existing_config, defaults) if existing_config else defaults
    config.session_host = resolved_host
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

    # 11. SessionStart hook: write the breadcrumb wrapper, prove the registered
    # command spawns, then register it (D4). The engine hook itself was already
    # probed in step 0b, so a failure here is wrapper-specific. The wrapper
    # always bakes the UNSHIMMED engine argv — it executes on the engine host.
    wrapper_name = hosts.wrapper_filename(resolved_host)
    wrapper_path = root / ".clauderizer" / wrapper_name
    changed = _rewrite_if_diff(
        wrapper_path,
        hosts.render_hook_wrapper(engine_hook, root=root,
                                  windows=wrapper_name.endswith(".cmd")),
        exact_newlines=True,
    )
    if changed and not wrapper_name.endswith(".cmd"):
        try:  # courtesy for direct execution; /bin/sh invocation needs no x-bit
            wrapper_path.chmod(wrapper_path.stat().st_mode | 0o755)
        except OSError:
            pass
    report.note("hook wrapper", wrapper_path, changed)
    registered_hook = hosts.hook_wrapper_invocation(root, resolved_host)
    if spawn_test:
        # No-arg digest probe from a NON-repo cwd (D-010/H-09): --version
        # answers before repo discovery, so only the digest path proves the
        # wrapper's anchor — an un-anchored wrapper is silent (exit 0) exactly
        # like the real executor chain made it, and must not register.
        probe = hosts.hook_digest_probe(registered_hook, cwd=hosts.non_repo_cwd())
        if probe.status == "fail":
            raise WiringRefused(
                f"the SessionStart wrapper failed its spawn test — hook registration "
                f"left unchanged.\n"
                f"  command: {' '.join(registered_hook)}  (from a non-repo cwd)\n"
                f"  probe:   {probe.detail}\n"
                f"  The wrapper was written to {wrapper_path} for inspection; the "
                f"engine command\n"
                f"  itself probed OK in the pre-write gate, so suspect the wrapper "
                f"shell (/bin/sh, cmd, wsl.exe) or the repo anchor."
            )
        if probe.status == "unverifiable":
            report.warnings.append(f"SessionStart wrapper unverifiable: {probe.detail}")
    changed = _register_hook(root / ".claude" / "settings.json", registered_hook)
    report.note("hook", root / ".claude" / "settings.json", changed)

    # 12. gitignore the disposable cache; reindex
    changed = _ensure_gitignore(root / ".gitignore", ".clauderizer/index.json")
    report.note(".gitignore", root / ".gitignore", changed)
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)

    return report


# --- helpers ------------------------------------------------------------------


def _rewrite_if_diff(path: Path, content: str, *, exact_newlines: bool = False) -> bool:
    """Write ``content`` if the file differs; report whether anything changed.

    ``exact_newlines`` writes/compares BYTES: executable wrapper scripts carry
    their newline convention as part of their contract (hook.sh must stay \\n
    even when written from a win32 host — the distro's sh chokes on \\r; the
    cmd template's \\r\\n must not become \\r\\r\\n via text-mode translation,
    which also broke init idempotency on win32 by making the read-back never
    equal the render).
    """
    if exact_newlines:
        data = content.encode("utf-8")
        if path.exists() and path.read_bytes() == data:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return True
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

    # Drop ANY existing clauderizer hook entry — direct entry-point wiring or
    # the D4 wrapper (hosts.is_hook_command is the shared matcher) — not just
    # an exact-string match. This makes re-running init with a changed
    # invocation (e.g. uvx -> venv path -> wrapper) REPLACE the hook instead of
    # appending a duplicate. Non-clauderizer hooks are preserved untouched.
    cleaned: list[dict] = []
    for group in sessionstart:
        kept = [h for h in group.get("hooks", []) if not hosts.is_hook_command(h.get("command", ""))]
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
