"""Marker-block losslessness (the O-04 field failure from the PhaseKeep repo).

A project section that ends up INSIDE the managed markers — the observed way:
content appended before the end marker at EOF — must never be deleted by a
re-init. The engine moves it below the block instead, under a visible banner.
"""

from clauderizer.markdown import sections

STANZA_V1 = "## Clauderizer\n\nOld stanza wording."
STANZA_V2 = "## Clauderizer\n\nNew stanza wording, revised for this release."

PROJECT_SECTION = (
    "---\n\n# PhaseKeep — the project\n\n"
    "## Key Files\n\nEverything the agent needs.\n"
)


def _block(content: str) -> str:
    return f"<!-- clauderizer:start -->\n{content}\n<!-- clauderizer:end -->"


def test_content_after_the_block_is_byte_preserved():
    text = _block(STANZA_V1) + "\n\n" + PROJECT_SECTION
    out = sections.upsert_marker_block(text, "clauderizer", STANZA_V2)
    assert PROJECT_SECTION in out
    assert "New stanza wording" in out
    assert sections.RECOVERY_BANNER not in out


def test_project_content_inside_the_block_is_moved_out_not_deleted():
    # The field failure: the whole project overview lived before the end marker.
    text = _block(STANZA_V1 + "\n\n" + PROJECT_SECTION.rstrip("\n"))
    out = sections.upsert_marker_block(text, "clauderizer", STANZA_V2)
    assert "# PhaseKeep — the project" in out
    assert "Everything the agent needs." in out
    assert sections.RECOVERY_BANNER in out
    # The recovered content now lives OUTSIDE the managed block…
    interior = sections.get_marker_block(out, "clauderizer")
    assert "PhaseKeep" not in interior
    # …so the next upsert is a plain idempotent replace.
    again = sections.upsert_marker_block(out, "clauderizer", STANZA_V2)
    assert again.count("# PhaseKeep — the project") == 1
    assert again.count(sections.RECOVERY_BANNER) == 1


def test_stanza_upgrade_recovers_nothing():
    # Replacing an older stanza whose wording changed must NOT spray "recovered"
    # noise — engine prose contains no H1, so the split finds nothing foreign.
    text = _block(STANZA_V1) + "\n"
    out = sections.upsert_marker_block(text, "clauderizer", STANZA_V2)
    assert sections.RECOVERY_BANNER not in out
    assert "Old stanza wording" not in out


def test_split_foreign_interior_grabs_the_separator():
    engine, foreign = sections.split_foreign_interior(
        STANZA_V1 + "\n\n---\n\n# User Section\nbody\n")
    assert engine.rstrip() == STANZA_V1
    assert foreign.startswith("---")
    assert "# User Section" in foreign


def test_init_rerun_preserves_project_content_end_to_end(temp_repo, capsys):
    from clauderizer import assets
    from clauderizer.markdown import writer
    from clauderizer.scaffold.init import init

    claude_md = temp_repo / "CLAUDE.md"
    stanza = assets.template_text("claude_stanza.md")
    # Reproduce the damaged layout: project content inside the managed block.
    writer.upsert_marker_block(claude_md, "clauderizer", stanza)
    damaged = claude_md.read_text(encoding="utf-8").replace(
        "<!-- clauderizer:end -->",
        "\n---\n\n# PhaseKeep — the project\n\nProject text that must survive.\n"
        "<!-- clauderizer:end -->")
    claude_md.write_text(damaged, encoding="utf-8")

    init(temp_repo, spawn_test=False)

    healed = claude_md.read_text(encoding="utf-8")
    assert "Project text that must survive." in healed
    assert sections.RECOVERY_BANNER in healed
    interior = sections.get_marker_block(healed, "clauderizer")
    assert "PhaseKeep" not in interior
    assert "moved it below the block" in capsys.readouterr().out
