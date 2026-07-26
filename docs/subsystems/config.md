---
id: subsys.config
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Config

`.clauderizer/config.toml` — the size, profile and host dial. Twelve modules read it, which makes its two least obvious properties (unknown-key preservation and loud parse failure) the load-bearing ones.

## Why TOML, and why a hand-rolled writer

Reading uses stdlib `tomllib`. Writing uses a small emitter, because the standard library has no TOML *writer* — it covers exactly the shapes stored here: tables of strings, bools, and lists of strings, and nothing else.

TOML rather than YAML for a machine-edited settings file: YAML's implicit typing (`no` → `False`, `1.10` → a float) is a liability when a config is rewritten by a program. Frontmatter inside docs stays YAML, per the procedure — different file, different audience, different failure mode.

## The surface

- **`Config`** — the dataclass. `version`, `size`, `host_profile`, `session_host`, `host_target`, `enabled_hosts`, the `paths` overrides, the memory thresholds, the module/ritual manifests, and the `active_gameplan` / `focus` / `assignment` pointers.
- **`Config.load(path)`** / **`Config.save(path)`** — the round trip.
- **`ConfigError`** — the config exists but cannot be parsed.
- **`merge_missing(existing, defaults)`** — return `existing` with any empty fields filled from `defaults`. This is what makes re-`init` non-destructive: a re-run fills gaps without overwriting choices.
- **`CONFIG_VERSION`** — the on-disk shape version. Distinct from `contract.CONTRACT_SCHEMA_VERSION` (the emitted JSON surface) and `graph.abstract_index.SCHEMA_VERSION` (an internal cache).
- **`SIZE_MANIFESTS`** — the default module/ritual manifest per size (`pet`, `standard`, …), mirroring the procedure's sizing matrix as a real dial rather than prose advice.

## Unknown keys survive a rewrite

`_MODELED_KEYS` lists the keys each section models. Anything else under a known section — and any unknown whole section — is captured into `Config.extra` and re-emitted **verbatim**. A config rewritten by an older engine, or by an engine that has not learned a newer key yet, does not lose it.

`[rituals]` is deliberately absent from `_MODELED_KEYS`: every key there is modeled by the dynamic `rituals` dict, so listing it would double-handle the same data.

## Failure is loud

`ConfigError` subclasses `ValueError` (so existing `except ValueError` handlers still catch it) and is raised for corrupt TOML, non-UTF-8 bytes, or a non-integer memory threshold. That last case is L-04: **a malformed threshold must be visible, never silently defaulted.** A config that silently falls back to defaults is a config whose settings quietly stop applying, and the user has no way to notice. `doctor` surfaces the error rather than the engine dying on a raw `TOMLDecodeError` traceback.

## Two host fields that are not the same thing

- **`host_target`** is a *preference* — which agent tool is assumed when runtime detection cannot tell (D-028/D-047). It defaults to `claude-code`, which keeps Claude Code's doctor and hook primary (INVARIANT-07).
- **`enabled_hosts`** is which hosts this repo is *wired for* (D-046). A missing `enabled` means `["*"]` — all project-level hosts — because exclusive wiring is the wrong default for a multi-AI repo, and a bare re-init expands rather than narrowing.

`session_host` is a third, orthogonal axis: which host spawns sessions (`native` or `windows-wsl:<distro>`). `None` means no init has recorded it; that is treated as native, but `doctor` can tell the difference and nudge a re-init rather than guessing.

## DAG position

Depends on nothing. Read by `cli`, `ops`, `mutations`, `listing`, `modernize`, `scaffold/init`, the hook handlers, and all of `rituals/` (`preflight`, `handoff`, `status_bundle`, `audit`, `critique`).
