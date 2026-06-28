---
id: subsys.profiles
type: subsystem
version: 0.3.0
status: completed
depends_on:
last_verified: 2026-06-20
---

# Profiles

The engine reads and writes Markdown and is **agnostic to the host project's language**. Everything language-specific — how to run tests, build, lint, typecheck, and how to read a baseline test count — lives in a **profile**: a TOML data file, not code. Adding a language is a new `<lang>.toml`, never an engine change.

> The profile is the **language** axis. It is orthogonal to a gameplan's **kind** (`subsys.kinds`, `kinds/*.toml`), which is the vocabulary + template + preflight *skin*. The two compose — a `campaign` kind on a `python` host resolves preflight from the kind (QA gates), not pytest.

## The profile shape

A profile is parsed into the `Profile` dataclass (`detect.py`) from a TOML file with a `name`, a `[detect]` section (marker `files` + a `weight`), `[commands]`, and `[preflight]`. `python.toml`:

```toml
name = "python"

[detect]
files = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"]
weight = 10

[commands]
test = "pytest -q"
build = ""
lint = "ruff check ."
typecheck = "mypy ."

[preflight]
baseline_test_regex = "(\\d+) passed"
```

The four recognized command kinds are `test`, `build`, `lint`, `typecheck`; `Profile.command(kind)` returns the (stripped) string, `""` when unset. `baseline_test_regex` is the pattern preflight uses to extract the passing-test count from test output.

## Shipped profiles

Five files ship in `src/clauderizer/profiles/`:

- **`node.toml`** — `npm test` / `npm run build` / `npm run lint` / `npm run typecheck`; baseline `(\d+) passing`. Markers: `package.json`, `tsconfig.json`, …
- **`python.toml`** — `pytest -q` / (no build) / `ruff check .` / `mypy .`; baseline `(\d+) passed`. Markers: `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`.
- **`go.toml`** — `go test ./...` / `go build ./...` / `go vet ./...`; baseline `ok\s`. Markers: `go.mod`, `go.sum`.
- **`ruby.toml`** — `bundle exec rspec` / (no build) / `bundle exec rubocop`; baseline `(\d+) examples?`. Markers: `Gemfile`, `.ruby-version`, `Rakefile`.
- **`generic.toml`** — the fallback. No markers (`weight = 0`), all commands empty; preflight degrades to git-state checks only, since empty commands are skipped.

## Auto-detect

`detect(repo_root)` scores every profile by the count of its `detect` files present in the repo root, scaled by `weight`, and returns `(best, alternatives)`. Profiles scoring `0` are dropped; if nothing scores, it returns `generic`. So `package.json` selects node, `pyproject.toml` python, `go.mod` go, `Gemfile` ruby — and a bare repo gets `generic`.

## Per-project override

`load_for_repo(name, lock_path)` loads the packaged profile, then **overlays** `.clauderizer/profile.lock.toml`. The lock is written once by `init` and preserved across re-runs; edit it to pin `test`/`build`/`lint`/`typecheck` or the baseline regex for a non-standard repo. Only non-empty lock values override packaged defaults; a missing lock — or one that fails to parse — falls back to the packaged profile (the parse error is surfaced by `doctor`, not silently fatal).

**0.4.0 escaping fix**: lock values are emitted as valid TOML basic strings with backslashes and quotes escaped. Regex baselines carry backslashes (`(\d+) passed`); emitting them raw produced an unparseable lock that `load_for_repo` then **silently ignored** (falling back to defaults). `to_lock_toml()` now escapes every value, with a round-trip regression test across all packaged profiles.

## DAG position

**Scaffold depends on profiles** — `init` detects the language and writes the lock. **Preflight (rituals) consumes a `Profile`** — it runs the `commands` for real and matches `baseline_test_regex` against the output; the engine never hardcodes a language. **Doctor** flags a `profile.lock.toml` that doesn't parse.
