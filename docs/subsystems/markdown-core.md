---
id: subsys.markdown-core
type: subsystem
version: 0.4.0
status: active
depends_on:
last_verified: 2026-07-19
---

# Markdown Core

The zero-dependency foundation every other write goes through: parse, edit, and serialize Clauderizer's markdown using the standard library only. It sits at the base of the Project DAG — nothing depends below it, and it depends on nothing (`depends_on:` is empty).

## The idempotent write contract

`writer.py` is the single sanctioned mutation path. Every tool that changes a doc calls a `writer` function; no tool does a free-form string replace. Each function returns `True` if the file changed on disk and `False` for a no-op — the idempotency signal the tests assert on.

**No-op suppression.** `_write_if_changed()` reads the current file, compares byte-for-byte, and writes only on a difference. Re-running `init`, an upsert, or a cascade never rewrites an unchanged file (and never touches its mtime).

**Body preservation.** `write_entity()` defaults `preserve_body=True`: for an existing file it merges the incoming frontmatter over the old (`dict.update`) and keeps the existing body verbatim, so a re-run or upsert never clobbers prose someone wrote. Only a fresh file receives the supplied `body`.

**Symlink refusal.** Every write path calls `refuse_if_symlink()` before touching disk: engine-owned writes must land inside the repo, so a symlinked target raises instead of following the link (the 1.0.5 hardening). Guards `_write_if_changed()`, `set_frontmatter_fields()`, and `create_if_absent()` alike.

The structured writers compose `frontmatter` + `sections` + `tables`: `upsert_section` / `append_to_section` (heading content), `upsert_marker_block` (marker stanzas), and the table-row writer (tracker tables). `create_if_absent()` scaffolds without ever overwriting.

## Frontmatter: a vendored YAML subset

`frontmatter.py` parses exactly the subset Clauderizer emits — no PyYAML, preserving the "drop into any repo with nothing installed" promise. Supported shapes are scalars (`str` / `int` / `bool` / `null`) and one-level-deep block lists of scalars:

```
key: scalar
key:
  - item
```

Fences are `---`. Unrecognized lines are ignored rather than fatal (robustness). `serialize()` round-trips (`parse → serialize → parse` is stable), quotes only values that need it, and emits `null` / `true` / `false` canonically.

## Structural, not substring

The trackers and lesson logic read structure, never substrings — the through-line behind the structural-robustness hardening (finding H-02, gameplan decisions D3/D8).

**Tables as contiguous blocks** (`tables.py`). A table block is one header row, one separator, then data rows with no blanks between — what external renderers require. Rows were historically appended as paragraphs (H-02), fracturing the table. The reader is tolerant (any pipe-prefixed line is a data row); the row writer replaces by key cell or appends, then rebuilds the whole block contiguous. The rebuild is idempotent and write-through (D3): any blessed touch heals a broken tracker, no one-off migration. Non-table lines (legends, prose) are preserved in order after the block.

**Lesson state as a trailing-marker grammar** (`lesson_state.py`, D8). A lesson's state lives in an anchored marker at the *end* of the line — `(obsolete <date>[: reason])` or `(promoted <date>: L-NN)` (anchored `$`) — plus legacy whole-line `~~strikethrough~~`. The word "obsolete" elsewhere in the text is inert: a lesson *about* obsolescence is not obsolete. Every consumer (memory gauge, handoff roll-ups, obsolete/promote/consolidate validation) parses through one shared `parse_state()` / `is_active()`; `mark()` is the only writer of these markers.

**Skill state mirrors the grammar** (`skill_state.py`, skill-awareness D1). A skill line's state is the same trailing-marker idea — `(obsolete <date>[: reason])` or `(superseded <date>: S-NN)` — with one divergence: skills *supersede* (a newer skill replaces an older one) where lessons *promote* (gameplan → project); skills are already project-level, so there is no promotion tier. Because a skill entry also carries structured fields (name, description, source), this module owns the `**S-NN.**` entry grammar too (`format_entry` / `parse_entry`); nothing substring-matches skill state.

## Marker blocks

`sections.upsert_marker_block()` owns only the content *between* `<!-- name:start -->` and `<!-- name:end -->`; everything outside the markers is byte-preserved. It is idempotent and creates the block at the end of the document when absent. This is the contract behind the CLAUDE.md / AGENTS.md Clauderizer stanzas and the cumulative handoffs — engine-rewritable regions embedded in files the user otherwise owns.

`sections.py` is pure (text in, new text out, no in-place mutation). `find_section()` matches a heading by title at any level and bounds its content at the next same-or-shallower heading; `append_to_section()` treats an empty body or a `_(…)_` scaffold placeholder as empty, so the first real entry replaces the placeholder instead of stacking under it.
