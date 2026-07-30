"""Who owns a doc — the structural boundary between engine state and project prose.

D-080: Clauderizer's docs are "more like configs" — engine state that happens to
be markdown — while the project's docs are prose a human authors. Until this
module existed the engine had no notion of the difference: every doc was just a
file in ``docs/``, so the engine scaffolded ``ARCHITECTURE.md``, ``SECURITY.md``
and ``GLOSSARY.md`` straight into the project's namespace and could not tell its
own memory from the human's writing. This is the filesystem realization of
D-039's two documentation layers, which was recorded 2026-06-23 and never built.

The map here is the single source of truth for ownership. Nothing infers it from
a filename at a call site.

**The identity default matters more than the map** (L-41): ``RepoPaths`` resolves
engine-owned docs through ``engine_docs_root``, whose default IS the project docs
directory. So introducing ownership moves no file and changes no path — every
existing repo resolves exactly what it resolved before — until a repo explicitly
opts into the split layout. That is what lets a breaking relocation land in
stages with a byte-identical digest at every step before the migration runs.
"""

from __future__ import annotations

#: Subdirectory (under the docs root) that holds ENGINE-owned docs once a repo
#: has opted into the split layout.
ENGINE_NAMESPACE = "clauderizer"

#: Config value naming the layout a repo is on. ``legacy`` is the identity.
LAYOUT_LEGACY = "legacy"
LAYOUT_SPLIT = "split"

ENGINE = "engine"
PROJECT = "project"
PRODUCT = "product"

#: Docs the ENGINE owns: the D-039 working-memory layer (only ``cz_*`` tools
#: write them) plus the engine's own shipped reference. These relocate.
ENGINE_DOCS = frozenset({
    "DECISIONS",
    "INVARIANTS",
    "LESSONS",
    "HARDENING",
    "SKILLS",
    "ENFORCEMENT",
    "GLOSSARY",       # the CLAUDERIZER-vocabulary glossary; see note below
})

#: Docs the PROJECT owns. The engine ships templates for these and will seed one
#: on request, but it never scaffolds them by default and never treats a file it
#: finds at these names as its own. Every measured collision lives here:
#: phasekeep owns its own SECURITY.md; the saas manifest claimed that name.
PROJECT_DOCS = frozenset({
    "ARCHITECTURE",
    "VISION",
    "TESTING",
    "SECURITY",
    "DEPLOYMENT",
    "SCHEMA",
    "REQUIREMENTS",
    "INCIDENTS",
    "DATASOURCES",
    "ENGINEERING-PRINCIPLES",
})

#: Engine-owned ENTITY directories (tracked docs with frontmatter), which travel
#: with the engine corpus rather than with the project's prose.
ENGINE_DIRS = ("features", "subsystems")

#: GLOSSARY is the one name that legitimately exists on BOTH sides, and it is the
#: general shape rather than a special case: a glossary of Clauderizer vocabulary
#: (gameplan, cascade, handoff, invariant, deferred) is genuinely useful to an
#: agent and belongs to the engine, while the project's domain glossary belongs to
#: the project. They are never merged, and a repo ends with both.
SPLIT_NAMES = frozenset({"GLOSSARY"})

#: GAMEPLAN-PROCEDURE.md is PRODUCT-layer (D-039: a human reads it to evaluate the
#: methodology) and — measured — is the file ``_procedure_drift`` reads to detect a
#: MAJOR version skew. Relocating it would destroy the one loud signal an older
#: engine trips on a migrated repo, so it stays at docs/gameplans/ (O-02).
PRODUCT_DOCS = frozenset({"GAMEPLAN-PROCEDURE"})


def _stem(name: str) -> str:
    return name[:-3] if name.endswith(".md") else name


def owner_of(name: str) -> str:
    """``engine`` | ``project`` | ``product`` for a doc name (with or without .md).

    An unknown name is PROJECT-owned. That default is deliberate and is the whole
    point: a doc the engine does not recognize belongs to the human, and the
    engine keeps its hands off it.
    """
    stem = _stem(name)
    if stem in ENGINE_DOCS:
        return ENGINE
    if stem in PRODUCT_DOCS:
        return PRODUCT
    return PROJECT


def is_engine_owned(name: str) -> bool:
    return owner_of(name) == ENGINE
