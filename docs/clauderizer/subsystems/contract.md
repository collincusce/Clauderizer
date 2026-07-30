---
id: subsys.contract
type: subsystem
version: 1.0.0
status: active
depends_on:
last_verified: 2026-07-25
---

# Contract

The external read-contract version stamp (PhaseKeep m0 ask, O-05). Twenty-four lines, one constant, one function — and it is the reason an external client can render Clauderizer's output without guessing.

## What it versions

Every ops-registry result carries an explicit `schema_version`. Because both transports execute the same registry (`subsys.ops`), that means every `--json` CLI output and every MCP tool result carries it too — the surfaces cannot drift on this any more than they can drift on anything else in the registry.

- **`CONTRACT_SCHEMA_VERSION`** — the version itself.
- **`stamp(result)`** — stamp it onto a dict result. Idempotent, and a non-dict passes through untouched, so it is safe to apply at any layer without auditing what is below.

## The compatibility rules

From the phasekeep proposal §6.2, and they are the contract, not a convention:

- additive changes bump the **minor**;
- breaking changes bump the **major**;
- clients ignore unknown fields, and degrade **explicitly** on a major they do not support.

The third rule is the one that earns the other two. A client that silently renders an unsupported major is a client that shows stale or wrong memory to a user who has no way to tell — which is the failure mode this whole system exists to prevent.

## What it is not

Three version numbers live in this engine and they are not interchangeable:

- `contract.CONTRACT_SCHEMA_VERSION` — the **emitted JSON surface only**, this module.
- `graph.abstract_index.SCHEMA_VERSION` — an internal cache format, disposable and rebuildable (INVARIANT-01).
- `config.CONFIG_VERSION` — the on-disk `.clauderizer/config.toml` shape.

Conflating them would tie a client-visible promise to an implementation detail. Keeping the client-facing one in a module that depends on nothing is what keeps that separation honest.

## DAG position

Depends on nothing. Consumed by `ops` (stamping every registry result), `cli` (the `--json` outputs), and `revision` — whose `.clauderizer/revision.json` is the one file external clients read directly, and therefore needs the same versioned promise.
