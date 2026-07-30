# Owner taxonomy — every templated doc name, classified

The table D-080 rests on. Every name the engine ships a template for, with its
owner and its destination. Nothing here is inferred at runtime from a filename;
this table becomes the engine's owner map in Phase 1.

## The three categories

| Category | Consumer | Who writes it | Destination |
|---|---|---|---|
| **engine** | agent | engine only (`cz_*` tools, or shipped verbatim) | `docs/clauderizer/` |
| **project** | human | the human authors it; engine seeds only on request | `docs/` (engine stops claiming) |
| **product** | human | engine ships it, human reads it to evaluate the method | stays put (D-039 product layer) |

## Every templated name

| Doc | Owner | Destination | Why |
|---|---|---|---|
| `DECISIONS` | engine | `docs/clauderizer/` | D-039 working-memory layer; only `cz_add_decision` writes it |
| `INVARIANTS` | engine | `docs/clauderizer/` | same; `cz_add_invariant` |
| `LESSONS` | engine | `docs/clauderizer/` | same; `cz_add_lesson` / `cz_promote_lesson`. On-demand (`ON_DEMAND_DOCS`) |
| `HARDENING` | engine | `docs/clauderizer/` | same; `cz_add_finding` |
| `SKILLS` | engine | `docs/clauderizer/` | same; `cz_register_skill`. On-demand |
| `ENFORCEMENT` | engine | `docs/clauderizer/` | the ladder for the *engine's* disciplines; shipped verbatim |
| `GLOSSARY` | **both** | split | Clauderizer vocabulary → `docs/clauderizer/GLOSSARY.md`; the project's domain glossary → `docs/GLOSSARY.md`. Never merged |
| `ARCHITECTURE` | project | `docs/` | the project's architecture, not the engine's. Generic name, high collision |
| `VISION` | project | `docs/` | the project's vision |
| `TESTING` | project | `docs/` | the project's test strategy |
| `SECURITY` | project | `docs/` | **measured collision**: phasekeep owns its own `SECURITY.md` |
| `DEPLOYMENT` | project | `docs/` | generic name, high collision |
| `SCHEMA` | project | `docs/` | generic name, high collision |
| `REQUIREMENTS` | project | `docs/` | generic name, high collision |
| `INCIDENTS` | project | `docs/` | generic name, high collision |
| `DATASOURCES` | project | `docs/` | generic name, high collision |
| `ENGINEERING-PRINCIPLES` | project | `docs/` | the project's principles |
| `GAMEPLAN-PROCEDURE` | product | `docs/gameplans/` — **stays** | D-039 product layer, **and** it is the file `_procedure_drift` reads: moving it destroys the one backward-compat signal an old engine trips (O-02) |

**11 of 18 rows are project-owned.** That is the size of the namespace the
engine has been claiming and will stop claiming.

## What "project" means operationally

The engine does **not** stop *supporting* these docs — a project that wants a
seeded `ARCHITECTURE.md` can still ask for one. It stops **scaffolding them by
default** and stops **listing them as modules it manages**. The distinction that
matters: the engine may no longer create a file in the project's namespace
without being asked, and may never treat a file it finds there as its own.

## The collision evidence (2026-07-30)

Surveyed across five real repos running Clauderizer. Engine memory interleaved
with project prose in every one; no way to tell them apart from the directory.

| Repo | Project's own docs | Engine docs in the same directory |
|---|---|---|
| `viderizer` (film production) | FILM-PROCEDURE, VOICE-CASTING-PROCEDURE, MIDJOURNEY-BINDER-PROCEDURE, CHARACTER-SHEET-PROCEDURE, RESEARCH-FIELD-NOTES, TOOL-LOCKINS, FIX-PLAN | ARCHITECTURE, DECISIONS, INVARIANTS, LESSONS, HARDENING, SKILLS, TESTING, VISION, ENFORCEMENT, GLOSSARY |
| `phasekeep` | CONPTY, PTY-FLOW-CONTROL, LAUNCH-RUNBOOK, BRANDING, NARRATIVE, RELEASING, **SECURITY**, phasekeep-proposal | (same engine set) |
| `marketing-studio` | CAMPAIGN, CAMPAIGN-PROCEDURE, EXECUTION-PATTERN, HIGGSFIELD-INDEX, STUDIO, USAGE, TOOL-LOCKINS | (same engine set) |
| `arena-security-audit` | AUDIT-REPORT, MONITORING | (same engine set) |
| `clauderizer-site` | — | (same engine set) |

`phasekeep`'s `SECURITY.md` is the sharpest case: the project owns that file,
and the `saas` size manifest claims that exact name. No damage occurred —
phasekeep is `standard`, where SECURITY is not in the manifest, and
`create_if_absent` never overwrites — but the name was claimable, which is the
defect.

## What 2.0.0 changed

`ensure_modules_current` (shipped 2.0.0) completes the size manifest on every
`upgrade`. It fixed a real bug — new doc modules previously reached only fresh
inits — but it also made the engine reach *more* eagerly into the project's
namespace, because completing the manifest means claiming every name in it.
Phase 2 scopes that action to engine-owned docs only, which is the correct
version of the same fix.
