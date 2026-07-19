# Testing

## Test Discipline

Tests live in `tests/` and run on `pytest` (the python host profile). Engine changes land
with their tests in the same change; the suite is the executable spec for the contracts
these docs claim. Several disciplines are enforced *by tests themselves*:

- **Bare-IO tripwire** (`test_io_discipline.py`) — no text-mode `read_text`/`write_text`/
  `open` without an explicit `encoding=` anywhere in `src` or `tests`. Newlines and
  encodings are content; a win32 locale decode could mojibake or raise.
- **Registry / tool-name parity** (`test_ops.py`, `test_mcp_tools.py`) — `ops.REGISTRY`,
  `tools_list.TOOL_NAMES`, and the live MCP tool surface are welded together so they cannot
  drift, and the no-MCP `clauderize ops` path executes the same functions.
- **Structural writes** (`test_structural_writes.py`, `test_sections.py`,
  `test_lesson_state.py`) — markdown is round-tripped, and tables / lesson-state are
  verified as *structure*, not substrings.
- **Concurrency** (`test_locking.py`) — the advisory write lock yields N sequential IDs and
  N surviving appends under N concurrent writer processes (H-05).
- **Wiring & release** (`test_hosts.py`, `test_hook_wrapper.py`, `test_release_check.py`) —
  the split-host wiring shapes, the breadcrumb wrapper, and the release ritual are pinned,
  including the false-green regressions that motivated them.
- Fixtures: `tests/fixtures/sample_repo/` is a minimal clauderized repo; `conftest.py`
  carries the shared scaffolding.

## Runner & Baseline

- **Runner:** `pytest` (from the python profile — `pytest -q`).
- **Baseline:** **912 tests** (907 passing, 5 skipped) as of 1.11.0. The suite runs — and
  passes — on every push across the CI matrix (ubuntu / macos / windows × py3.11–3.13), with
  the native win32 cmd wrapper executed for real, not simulated. Per-release counts are
  recorded in the [CHANGELOG](../CHANGELOG.md); treat that as the source of truth over any
  number quoted here.

## Coverage Policy

Every engine contract a doc asserts should have a test that fails if the contract breaks —
especially idempotent / non-clobbering writes, append-only memory, ID auto-numbering, the
write lock under concurrency, profile command/baseline parsing, pre-flight check behavior,
and the wiring launchability/identity probes. New failure classes get a regression test that
reproduces the exact failure *before* the fix lands — each resolved finding in
[HARDENING.md](HARDENING.md) cites the test that pins it.
