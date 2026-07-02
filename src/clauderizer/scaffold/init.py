"""``clauderize init`` — drop Clauderizer into a repo.

Every step is idempotent: re-running ``init`` fills gaps and refreshes
engine-owned files, but never clobbers user content. The second run on an
unchanged repo produces zero diffs (a tested invariant).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .. import assets, hosts, hosttargets
from ..config import Config, merge_missing
from ..graph import abstract_index, index
from ..markdown import writer
from ..paths import RepoPaths, resolve
from ..profiles import detect

# Zero-install fallback when nothing is on PATH. uvx resolves the package on
# demand. Overridable with --run-cmd "pipx run clauderizer". The -q matters:
# on a cold cache uv prints resolution progress to stderr, which the hook
# wrapper reroutes into stdout (L-07) — straight into session context, and in
# front of the --version identity line the probes parse (stranger-readiness
# Phase 0, cache-clean walk).
DEFAULT_RUN = ["uvx", "-q", "--from", "clauderizer"]


class WiringRefused(RuntimeError):
    """A composed wiring command failed its spawn test; nothing was written.

    The H-04 regression guard: init must never write a command the session
    host cannot launch (e.g. a multi-word --run-cmd that composes an invalid
    subcommand like ``clauderize clauderizer-mcp``).
    """


def _under_uv_cache(p: Path) -> bool:
    """Is this path inside uv's cache — i.e. a uvx ephemeral tool environment?

    ``uvx --from clauderizer clauderize init`` runs from an env under uv's
    CACHE. Wiring those console-script paths into ``.mcp.json`` / the hook
    wrapper produces wiring that dies on ``uv cache clean`` — doctor drift
    plus engine-unreachable breadcrumbs until a re-init (found live in the
    stranger-readiness Phase 0 walk). Such paths must never be wired; the
    durable zero-install ``uvx --from clauderizer`` form is.
    """
    try:
        rp = p.resolve()
    except OSError:
        rp = p
    if "archive-v0" in rp.parts:  # uvx ephemeral envs live here on every OS
        return True
    candidates: list[Path] = []
    env_cache = os.environ.get("UV_CACHE_DIR")
    if env_cache:
        candidates.append(Path(env_cache))
    if sys.platform == "win32":
        lad = os.environ.get("LOCALAPPDATA")
        if lad:
            candidates.append(Path(lad) / "uv" / "cache")
    else:
        try:
            candidates.append(Path.home() / ".cache" / "uv")
        except RuntimeError:
            pass
    for c in candidates:
        try:
            if rp.is_relative_to(c.resolve()):
                return True
        except (OSError, ValueError):
            continue
    return False


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
    # interpreter's dir for a venv). NEVER wire a uvx ephemeral env (it dies on
    # `uv cache clean`); fall back to PATH lookup, then the durable uvx form.
    bindir = Path(sys.executable).parent

    def _script(name: str) -> Path | None:
        for candidate in (bindir / f"{name}.exe", bindir / name):
            if candidate.exists():
                return candidate
        return None

    if not _under_uv_cache(bindir):
        mcp = _script("clauderizer-mcp")
        hook = _script("clauderizer-hook")
        if mcp and hook:
            return [str(mcp)], [str(hook)]
    which_mcp = shutil.which("clauderizer-mcp")
    which_hook = shutil.which("clauderizer-hook")
    if (which_mcp and which_hook
            and not _under_uv_cache(Path(which_mcp))):
        # (uvx prepends its ephemeral bin to PATH, so which() finds the same
        # dying paths the bindir check just refused — filter those too)
        return [which_mcp], [which_hook]
    # Absolutize uvx when present: hooks and shimmed commands run in non-login
    # shells whose PATH may not include ~/.local/bin (observed live on WSL).
    uvx = shutil.which(DEFAULT_RUN[0]) or DEFAULT_RUN[0]
    run = [uvx, *DEFAULT_RUN[1:]]
    # The MCP server needs the optional `mcp` extra; the hook and CLI do not. The
    # zero-install uvx path must request `clauderizer[mcp]` for the SERVER command
    # only — `--from clauderizer` never installs the extra, so the wired server
    # printed the missing-package notice and exited without serving (H-14, found
    # live across the pet/standard/saas stranger-readiness dogfood). The hook
    # command stays extra-free so its cold resolve downloads nothing it can't use.
    mcp_run = [*run[:-1], f"{run[-1]}[mcp]"]
    return [*mcp_run, "clauderizer-mcp"], [*run, "clauderizer-hook"]


@dataclass
class InitReport:
    repo: str
    host_profile: str = ""
    size: str = ""
    session_host: str = ""
    host_target: str = ""
    host_target_auto: bool = False  # defaulted to claude-code with no choice made
    actions: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # Nudges that aren't problems — e.g. the onboarding advisory (D-044): the
    # repo has real docs and the scaffolded Clauderizer docs are still
    # placeholders, so the natural next step is seeding.
    advisories: list[str] = field(default_factory=list)

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
    host_target: str | None = None,
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

    # 0a. host target (D-028, the THIRD host axis): explicit flag > what config
    # already records > cheap auto-detection > claude-code. Validated up front so
    # an unknown name fails friendly (listing valid hosts) before anything writes
    # — never a KeyError deep in the emitter table (P8 exit criterion).
    resolved_target = (
        host_target
        or (existing_config.host_target if existing_config else None)
        or hosttargets.detect_host_target(root)
    )
    resolved_target = hosttargets.parse_host_target(resolved_target)
    report.host_target = resolved_target
    # Flag the default-with-no-choice case so the CLI can nudge that other hosts
    # exist — a presentation hint, NOT a wiring warning (report.warnings stays
    # reserved for the spawn-probe verdicts existing callers assert on).
    report.host_target_auto = (
        host_target is None and existing_config is None
        and resolved_target == hosttargets.CLAUDE_CODE
    )

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
    config.host_target = resolved_target
    # Init is an upgrade moment (D-042): stamp the corpus with this engine's
    # procedure version so status can tell a current corpus from a stale one.
    from .. import PROCEDURE_VERSION as _PROC_V

    config.procedure_version = _PROC_V
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

    # 6b. onboarding advisory (D-044): this repo already has documentation and
    # the Clauderizer docs are still scaffold placeholders — say so once, with
    # the next step. Detection is read-only; the engine never seeds anything.
    from .. import onboard as _onboard

    _unseeded = _onboard.unseeded_docs(paths)
    if _unseeded:
        _cands = _onboard.spec_candidates(paths)
        if _cands:
            report.advisories.append(
                f"this repo has {len(_cands)} existing doc(s) that look like specs "
                f"(e.g. {_cands[0]['path']}) while {len(_unseeded)} scaffolded "
                f"Clauderizer doc(s) are still placeholders — have your agent run "
                f"cz_onboard (or the clauderizer-onboard skill) to seed memory from them")

    # 7. optional first gameplan
    if gameplan:
        from .. import mutations

        r = mutations.create_gameplan(paths, gameplan)
        config.active_gameplan = r["gameplan_id"]
        _rewrite_if_diff(paths.config_file, config.to_toml())
        report.note("gameplan", r["dir"], bool(r["files_changed"]))

    # 8. CLAUDE.md stanza (marker block; preserves the rest)
    stanza = assets.template_text("claude_stanza.md")
    changed = writer.upsert_marker_block(paths.claude_md, "clauderizer", stanza)
    report.note("CLAUDE.md", paths.claude_md, changed)

    # 8b. AGENTS.md stanza — the SAME host-agnostic marker block, so kimi
    # (KIMI_AGENTS_MD) and any other AGENTS.md-aware harness get Clauderizer too
    # (D2). One source stanza for both files means they cannot drift (L-16).
    changed = writer.upsert_marker_block(paths.agents_md, "clauderizer", stanza)
    report.note("AGENTS.md", paths.agents_md, changed)

    # 9. install skills (engine-owned: refresh)
    for skill_dir in assets.skill_dirs():
        dest_dir = root / ".claude" / "skills" / skill_dir.name
        for src in skill_dir.iterdir():
            if src.is_file():
                changed = _rewrite_if_diff(dest_dir / src.name, src.read_text(encoding="utf-8"))
                report.note(f"skill:{skill_dir.name}", dest_dir / src.name, changed)

    # 10–11b. Host-target wiring (P8, A-001). claude-code keeps the original
    # .mcp.json + SessionStart-hook + kimi-setup wiring byte-for-byte
    # (INVARIANT-07); every other host routes to its per-host emitters (P4/P5),
    # finally reachable through init. The AGENTS.md floor, skills, and docs above
    # are host-agnostic and already written, so a non-claude host gets BOTH the
    # floor and its tools (no floor-but-no-tools).
    if resolved_target == hosttargets.CLAUDE_CODE:
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

        # 11b. kimi-code setup snippet (D2): the [[hooks]] entries + MCP guidance the
        # user merges into their kimi config. Non-destructive — a project file under
        # .clauderizer/, never the global ~/.kimi/config.toml. kimi injects EVERY
        # hook's stdout, so all four events are wired here (vs Claude Code's two — D1).
        changed = _rewrite_if_diff(paths.kimi_setup,
                                   _render_kimi_setup(registered_hook, mcp_cmd))
        report.note("kimi-setup", paths.kimi_setup, changed)

        # 11c. Path-safety for the local wiring (O-06/D-031, security review HIGH).
        # claude-code's .mcp.json prefers your LOCAL install for launch reliability,
        # so it can carry a machine-specific command (a venv path, or a wsl.exe shim
        # for a split host) — dead on any other machine and a path leak if committed.
        # The cross-host emitters REFUSE such commands (their configs are meant to be
        # shared); .mcp.json is your local wiring, so we keep it but gitignore it when
        # it is not portable — the same protection the dogfood repo uses. (A portable
        # uvx command stays committable. .claude/settings.json may also hold your own
        # settings, so it is left for you to gitignore — see docs/TRUST.md.)
        if not hosttargets.is_path_safe(mcp_cmd):
            gi = _ensure_gitignore(root / ".gitignore", paths.mcp_json.name)
            report.note(".gitignore (.mcp.json — local wiring, not committable)",
                        root / ".gitignore", gi)
    else:
        # A non-claude host: emit its MCP registration (or setup guide for a
        # guide-only host), the native floor where it does not read AGENTS.md, and
        # its hook setup guide. The Claude-Code-only .mcp.json key and
        # .claude/settings.json hooks are NOT written — that wiring is dead here.
        for res in hosttargets.emit_host_wiring(resolved_target, root):
            report.note(f"{res.label}:{resolved_target}", res.path, res.changed)

    # 12. gitignore the disposable caches; build the graph + abstract indexes
    gi = root / ".gitignore"
    changed = _ensure_gitignore(gi, ".clauderizer/index.json")
    changed = _ensure_gitignore(gi, ".clauderizer/abstract_index.json") or changed
    report.note(".gitignore", gi, changed)
    graph = index.build(paths.docs)
    index.write_cache(graph, paths.index_file, paths.docs)
    abstract_index.write_cache(abstract_index.build(paths), paths.abstract_index_file)

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
    writer.refuse_if_symlink(path)
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
    writer.refuse_if_symlink(mcp_json)
    mcp_json.parent.mkdir(parents=True, exist_ok=True)
    mcp_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


# The Claude Code hook events the wrapper is registered under (D-025/D1). The
# SAME wrapper command serves both: SessionStart is the cold-start digest (and
# re-fires with source=compact, so it also covers post-compaction re-injection);
# UserPromptSubmit runs the analyze gate per prompt. PreCompact/PostCompact are
# intentionally absent — Claude Code does not inject their stdout into context
# (D1), so registering them would be dead wiring. The engine's dispatcher
# implements every event regardless of which a host fires.
HOOK_EVENTS = ("SessionStart", "UserPromptSubmit")


def _register_hook(settings_json: Path, hook_argv: list[str],
                   events: tuple[str, ...] = HOOK_EVENTS) -> bool:
    data = {}
    if settings_json.exists():
        try:
            data = json.loads(settings_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    hook_cmd = " ".join(hook_argv)
    hooks = data.setdefault("hooks", {})

    for event in events:
        # Drop ANY existing clauderizer hook entry — direct entry-point wiring or
        # the D4 wrapper (hosts.is_hook_command is the shared matcher) — not just
        # an exact-string match. This makes re-running init with a changed
        # invocation (e.g. uvx -> venv path -> wrapper) REPLACE the hook instead
        # of appending a duplicate. Non-clauderizer hooks under this event are
        # preserved untouched.
        cleaned: list[dict] = []
        for group in hooks.get(event, []):
            kept = [h for h in group.get("hooks", [])
                    if not hosts.is_hook_command(h.get("command", ""))]
            if kept:
                cleaned.append({**group, "hooks": kept})
            elif not group.get("hooks"):
                cleaned.append(group)  # preserve unrelated empty groups verbatim
        cleaned.append({"hooks": [{"type": "command", "command": hook_cmd}]})
        hooks[event] = cleaned

    new_text = json.dumps(data, indent=2) + "\n"
    if settings_json.exists() and settings_json.read_text(encoding="utf-8") == new_text:
        return False
    writer.refuse_if_symlink(settings_json)
    settings_json.parent.mkdir(parents=True, exist_ok=True)
    settings_json.write_text(new_text, encoding="utf-8")
    return True


# kimi injects every hook's stdout into context (unlike Claude Code, which drops
# PreCompact/PostCompact stdout — D1), so the generated snippet wires all four
# events. The same wrapper command serves each; the engine dispatches on the
# payload's hook_event_name and stays silent when it has nothing to add.
_KIMI_HOOK_EVENTS = ("SessionStart", "PreCompact", "PostCompact", "UserPromptSubmit")


def _render_kimi_setup(hook_argv: list[str], mcp_argv: list[str]) -> str:
    """The non-destructive kimi-code wiring guide written to .clauderizer/
    kimi-setup.md (D2). TOML literal strings (single quotes) carry the commands
    verbatim so Windows backslashes are not read as escapes."""
    hook_cmd = " ".join(hook_argv)
    mcp_cmd = " ".join(mcp_argv)
    hook_blocks = "\n\n".join(
        f"[[hooks]]\nevent = \"{ev}\"\ncommand = '{hook_cmd}'"
        for ev in _KIMI_HOOK_EVENTS
    )
    return f"""# Clauderizer × kimi-code setup

Clauderizer is host-agnostic — the engine, the MCP server, and the hook digest
all work under kimi-code. This file is generated by `clauderize init` (rewritten
on every run; safe to delete). It is NOT applied automatically: Clauderizer never
edits your global `~/.kimi/config.toml`. Copy what you need.

## 1. Skills — already working

kimi-code reads `.claude/skills/` (its "brand group"), so the Clauderizer skills
this repo ships are already available in kimi. Nothing to do.

## 2. AGENTS.md — already written

`clauderize init` injects the Clauderizer stanza into `AGENTS.md` (inside a
`<!-- clauderizer -->` marker block), which kimi loads via `KIMI_AGENTS_MD`.

## 3. Hooks — add to `~/.kimi/config.toml`

kimi adds a hook's stdout to context on exit 0 for every event, so all four are
useful here (Claude Code drops PreCompact/PostCompact stdout, so it wires only
SessionStart + UserPromptSubmit). One command serves all four — the engine routes
on `hook_event_name`:

```toml
{hook_blocks}
```

## 4. MCP server — register the `clauderizer` server

This repo's `.mcp.json` already defines the server command:

```
{mcp_cmd}
```

Register it with kimi (`kimi mcp`, or `/mcp-config` in a session). kimi's
MCP-server TOML schema is not documented at the time of writing (tracked as
gameplan open item O-01), so this step is manual — add an equivalent entry to
your kimi MCP configuration pointing at that command.
"""


def _ensure_gitignore(gitignore: Path, line: str) -> bool:
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if line in existing.splitlines():
        return False
    new = existing.rstrip("\n") + ("\n" if existing else "") + line + "\n"
    writer.refuse_if_symlink(gitignore)
    gitignore.write_text(new, encoding="utf-8")
    return True
