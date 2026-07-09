"""Load and write ``.clauderizer/config.toml`` — the size/profile dial.

Reading uses stdlib ``tomllib``. Writing uses a tiny emitter (stdlib has no
TOML writer) that covers exactly the shapes we store: tables of strings, bools,
and lists of strings. Keeping the config in TOML avoids YAML's ambiguity for
machine-edited settings; frontmatter inside docs stays YAML per the procedure.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_VERSION = "1"


class ConfigError(ValueError):
    """``.clauderizer/config.toml`` exists but cannot be parsed — corrupt TOML,
    non-UTF-8 bytes, or a non-integer memory threshold (L-04: a malformed
    threshold must be visible, never silently defaulted). Raised by
    :meth:`Config.load` so callers report it cleanly instead of dying on a raw
    ``TOMLDecodeError``/``UnicodeDecodeError`` traceback. Subclasses ``ValueError``
    so any existing ``except ValueError`` still catches it."""


# The keys each config section models. Anything else under a known section, and
# any unknown whole section, is captured into Config.extra and re-emitted verbatim
# so a rewrite never drops it. [rituals] is intentionally absent — every key there
# is modeled by the dynamic ``rituals`` dict.
_MODELED_KEYS: dict[str, set[str]] = {
    "clauderizer": {"version", "size", "preflight_checks", "preflight_advisory",
                    "procedure_version"},
    "host": {"profile", "session_host", "target", "enabled"},
    "paths": {"docs", "gameplans"},
    "memory": {"active_lessons_warn", "project_lessons_warn"},
    "modules": {"enabled"},
    "active_gameplan": {"id"},
    "focus": {"id"},
}
_KNOWN_SECTIONS = set(_MODELED_KEYS) | {"rituals"}

# Default module/ritual manifests per size. Mirrors the procedure's sizing
# matrix, but as a real dial instead of prose advice.
SIZE_MANIFESTS: dict[str, dict[str, Any]] = {
    "pet": {
        "modules": ["VISION"],
        "rituals": {"preflight": True, "cascade": False, "amendments": False},
        "preflight_checks": ["clean_tree", "tests"],
    },
    "standard": {
        "modules": [
            "VISION",
            "ARCHITECTURE",
            "DECISIONS",
            "INVARIANTS",
            "TESTING",
            "HARDENING",
        ],
        "rituals": {"preflight": True, "cascade": True, "amendments": False},
        "preflight_checks": [
            "branch_base",
            "clean_tree",
            "tests",
            "build",
            "deps_spotcheck",
            "branch_creation",
            "cascade_hygiene",
            "handoff_presence",
        ],
    },
    "saas": {
        "modules": [
            "VISION",
            "REQUIREMENTS",
            "ARCHITECTURE",
            "ENGINEERING-PRINCIPLES",
            "DEPLOYMENT",
            "DATASOURCES",
            "SCHEMA",
            "SECURITY",
            "TESTING",
            "HARDENING",
            "INCIDENTS",
            "DECISIONS",
            "INVARIANTS",
            "GLOSSARY",
        ],
        "rituals": {"preflight": True, "cascade": True, "amendments": True},
        "preflight_checks": [
            "branch_base",
            "clean_tree",
            "tests",
            "build",
            "deps_spotcheck",
            "branch_creation",
            "cascade_hygiene",
            "handoff_presence",
        ],
    },
}


@dataclass
class Config:
    version: str = CONFIG_VERSION
    size: str = "standard"
    host_profile: str = "generic"
    # Which host spawns Claude Code sessions: "native" or "windows-wsl:<distro>"
    # (D3, agent-autonomy). None = recorded by no init yet — treated as native,
    # but doctor can tell the difference and nudge a re-init.
    session_host: str | None = None
    # Session-agent preference (D-028 / D-047): which agent tool is assumed when
    # runtime detection cannot tell. NOT the exclusive wiring identity — see
    # enabled_hosts. Default keeps Claude Code doctor/hook primary (INVARIANT-07).
    host_target: str = "claude-code"
    # Which hosts this repo is WIRED for (D-046). ["*"] = all project-level hosts
    # (the multi-AI default). A concrete list scopes the footprint; legacy configs
    # without this key load as ["*"] so the next bare init expands (O-03).
    enabled_hosts: list[str] = field(default_factory=lambda: ["*"])
    docs: str = "docs"
    gameplans: str = "docs/gameplans"
    modules: list[str] = field(default_factory=list)
    rituals: dict[str, bool] = field(default_factory=dict)
    preflight_checks: list[str] = field(default_factory=list)
    preflight_advisory: list[str] = field(default_factory=list)
    # The GAMEPLAN-PROCEDURE version this corpus was last modernized to (D-042).
    # Stamped by `clauderize init` / `clauderize upgrade`; "" = a legacy corpus
    # that predates stamping — the status digest then surfaces one modernization
    # line until the corpus is brought current. Never gates anything.
    procedure_version: str = ""
    # The default-target gameplan for status / do-phase / handoff — the "focus"
    # (D2 of concurrent-multi-axis-gameplans). Stored canonically as ``focus``;
    # ``active_gameplan`` remains a property alias (below) so the ~40 existing call
    # sites and ``config.active_gameplan = gid`` writes keep working unchanged
    # while the config file migrates [active_gameplan] -> [focus]. The set of OPEN
    # gameplans is derived (status_bundle.portfolio), never stored — only the one
    # focus pointer persists.
    focus: str | None = None
    # [memory] — D-009 is pressure + visibility, not caps: above these counts
    # the status digest nudges toward consolidation; nothing is auto-pruned.
    # active_lessons_warn: the current gameplan's active lessons (every handoff
    # carries all of them). project_lessons_warn: docs/LESSONS.md L-entries
    # (these ride in every handoff across ALL gameplans, O2).
    active_lessons_warn: int = 12
    project_lessons_warn: int = 20
    # Any config keys/sections this engine version does NOT model, captured on
    # load and re-emitted by to_toml so a rewrite never silently DROPS a field
    # the engine doesn't recognize. Forward/cross-version safe: a newer config
    # rewritten by this engine keeps its newer fields, and a hand-added key
    # survives — closing the host_target-strip class (P9) for every config field,
    # not just host_target. ([rituals] is excluded — it is fully modeled.)
    extra: dict = field(default_factory=dict)

    @classmethod
    def for_size(cls, size: str, host_profile: str = "generic") -> "Config":
        manifest = SIZE_MANIFESTS.get(size, SIZE_MANIFESTS["standard"])
        return cls(
            size=size,
            host_profile=host_profile,
            modules=list(manifest["modules"]),
            rituals=dict(manifest["rituals"]),
            preflight_checks=list(manifest["preflight_checks"]),
        )

    def ritual_enabled(self, name: str) -> bool:
        return bool(self.rituals.get(name, False))

    @property
    def active_gameplan(self) -> str | None:
        """Back-compat alias for :attr:`focus` (D2): every existing
        ``config.active_gameplan`` read and ``config.active_gameplan = gid`` write
        keeps working unchanged; new code uses ``focus``. Not a dataclass field
        (no annotation) so it is invisible to ``__init__``/``asdict``."""
        return self.focus

    @active_gameplan.setter
    def active_gameplan(self, value: str | None) -> None:
        self.focus = value

    @classmethod
    def load(cls, path: Path) -> "Config":
        # Wrap the parse so a corrupt config surfaces as a clean, named ConfigError
        # rather than a raw TOMLDecodeError/UnicodeDecodeError traceback. The hook
        # already degrades (dispatch catches → breadcrumb → exit 0); this lets the
        # CLI (doctor/status/reindex) and MCP report the corruption instead of
        # crashing on it (P11 failure-mode hardening).
        try:
            with path.open("rb") as fh:
                raw = tomllib.load(fh)
            cz = raw.get("clauderizer", {})
            host = raw.get("host", {})
            paths = raw.get("paths", {})
            modules = raw.get("modules", {})
            rituals = raw.get("rituals", {})
            # [focus] is canonical; fall back to the legacy [active_gameplan]
            # section (the migration — an old repo keeps its pointer, a rewrite
            # re-emits it under [focus]). focus wins if a half-migrated file has both.
            active = raw.get("focus") or raw.get("active_gameplan", {})
            memory = raw.get("memory", {})
            # Capture anything this engine doesn't model so to_toml can re-emit it
            # (forward/cross-version safe — never drop an unrecognized field).
            extra: dict = {}
            for section, body in raw.items():
                if not isinstance(body, dict) or section == "rituals":
                    continue
                modeled = _MODELED_KEYS.get(section)
                if modeled is None:
                    extra[section] = dict(body)              # unknown whole section
                else:
                    leftover = {k: v for k, v in body.items() if k not in modeled}
                    if leftover:
                        extra[section] = leftover            # unknown keys in a known section
            return cls(
                version=str(cz.get("version", CONFIG_VERSION)),
                size=str(cz.get("size", "standard")),
                host_profile=str(host.get("profile", "generic")),
                session_host=(str(host["session_host"]) if host.get("session_host") else None),
                host_target=str(host.get("target", "claude-code")),
                # Missing `enabled` → multi default (D-046); bare re-init expands.
                enabled_hosts=list(host["enabled"]) if host.get("enabled") is not None
                else ["*"],
                docs=str(paths.get("docs", "docs")),
                gameplans=str(paths.get("gameplans", "docs/gameplans")),
                modules=list(modules.get("enabled", [])),
                rituals={k: bool(v) for k, v in rituals.items()},
                preflight_checks=list(cz.get("preflight_checks", [])),
                preflight_advisory=list(cz.get("preflight_advisory", [])),
                procedure_version=str(cz.get("procedure_version", "")),
                focus=(active.get("id") or None),
                # int() raises on garbage — a malformed threshold must be visible,
                # never silently replaced by a default (L-04).
                active_lessons_warn=int(memory.get("active_lessons_warn", 12)),
                project_lessons_warn=int(memory.get("project_lessons_warn", 20)),
                extra=extra,
            )
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise ConfigError(
                f"{path} is malformed ({exc}); fix it or re-run `clauderize init`"
            ) from exc

    def to_toml(self) -> str:
        # ex(section) re-emits any captured unknown keys for a known section. Empty
        # for a config with no extras, so to_toml stays byte-identical to before
        # the preservation change (init idempotency / INVARIANT-07 unaffected).
        def ex(section: str) -> list[str]:
            return [_toml_kv(k, v) for k, v in (self.extra.get(section) or {}).items()]

        lines = [
            "[clauderizer]",
            f'version = "{self.version}"',
            f'size = "{self.size}"',
            _toml_kv("preflight_checks", self.preflight_checks),
            _toml_kv("preflight_advisory", self.preflight_advisory),
            # Emitted only once stamped, so a legacy config rewrite stays
            # byte-identical until init/upgrade deliberately stamps it.
            *([f'procedure_version = "{self.procedure_version}"']
              if self.procedure_version else []),
            *ex("clauderizer"),
            "",
            "[host]",
            f'profile = "{self.host_profile}"',
            f'target = "{self.host_target}"',
            _toml_kv("enabled", self.enabled_hosts or ["*"]),
            *([f'session_host = "{self.session_host}"'] if self.session_host else []),
            *ex("host"),
            "",
            "[paths]",
            f'docs = "{self.docs}"',
            f'gameplans = "{self.gameplans}"',
            *ex("paths"),
            "",
            "[memory]",
            f"active_lessons_warn = {self.active_lessons_warn}",
            f"project_lessons_warn = {self.project_lessons_warn}",
            *ex("memory"),
            "",
            "[modules]",
            _toml_kv("enabled", self.modules),
            *ex("modules"),
            "",
            "[rituals]",
        ]
        for k, v in self.rituals.items():
            lines.append(f"{k} = {'true' if v else 'false'}")
        # Migrate the pointer to [focus]; the legacy [active_gameplan] section is
        # no longer emitted (an old repo's pointer was read into self.focus above).
        # ex("active_gameplan") re-emits any stray non-"id" keys a legacy section
        # carried, so a rewrite still never drops an unrecognized field.
        lines += ["", "[focus]", f'id = "{self.focus or ""}"',
                  *ex("focus"), *ex("active_gameplan"), ""]
        # unknown WHOLE sections, preserved verbatim (forward/cross-version safe).
        for section, body in self.extra.items():
            if section in _KNOWN_SECTIONS:
                continue
            lines.append(f"[{section}]")
            lines += [_toml_kv(k, v) for k, v in body.items()]
            lines.append("")
        return "\n".join(lines)


def _toml_scalar(v: Any) -> str:
    if isinstance(v, bool):            # bool is an int subclass — check it first
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return f'"{v}"'


def _toml_kv(key: str, value: Any) -> str:
    if isinstance(value, list):
        return f"{key} = [{', '.join(_toml_scalar(v) for v in value)}]"
    return f"{key} = {_toml_scalar(value)}"


def merge_missing(existing: Config, defaults: Config) -> Config:
    """Return ``existing`` with any empty fields filled from ``defaults``.

    Used by ``init`` re-runs so user edits are never overwritten — only gaps are
    filled in.
    """
    return Config(
        version=existing.version or defaults.version,
        size=existing.size or defaults.size,
        host_profile=existing.host_profile or defaults.host_profile,
        session_host=existing.session_host or defaults.session_host,
        host_target=existing.host_target or defaults.host_target,
        enabled_hosts=list(existing.enabled_hosts)
        if existing.enabled_hosts else list(defaults.enabled_hosts or ["*"]),
        docs=existing.docs or defaults.docs,
        gameplans=existing.gameplans or defaults.gameplans,
        modules=existing.modules or defaults.modules,
        rituals=existing.rituals or defaults.rituals,
        preflight_checks=existing.preflight_checks or defaults.preflight_checks,
        preflight_advisory=existing.preflight_advisory or defaults.preflight_advisory,
        procedure_version=existing.procedure_version or defaults.procedure_version,
        focus=existing.focus or defaults.focus,
        # ints always carry a value after load (defaults applied there); `or`
        # would clobber a deliberate 0 ("warn always"), so pass through as-is.
        active_lessons_warn=existing.active_lessons_warn,
        project_lessons_warn=existing.project_lessons_warn,
        # carry the existing config's unmodeled keys forward (an init re-run must
        # not drop a field the engine doesn't recognize — the whole point).
        extra=existing.extra or defaults.extra,
    )
