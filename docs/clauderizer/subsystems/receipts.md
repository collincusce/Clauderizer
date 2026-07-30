---
id: subsys.receipts
type: subsystem
version: 0.1.0
status: active
depends_on:
  - subsys.paths
  - subsys.session
last_verified: 2026-07-27
---

# Receipts

Seen-vs-open engagement receipts (D-073): per-machine, gitignored, disposable
labeling state in `.clauderizer/seen.local.jsonl` — the sole sanctioned write on
a read-declared op. The digest's open findings/open items lines re-bill every
unresolved id every session with no engagement axis; receipts add that axis as
pure labeling (never-engaged vs engaged-but-open, ANY-reader), the D-069
engagement detector. Both buckets always render every id (D-068 drop-nothing);
losing the file loses labels, never canonical memory (D-067). Receipts land
ONLY on genuine engagement — cz_get success and the resolve/check writes — at
the ops REGISTRY seam (the refusal-journal precedent), never inside library
read functions (C-02), and never from handoff/phase-context assembly (the
false-seen risk the vetting named). Advisory throughout (INVARIANT-05);
`status_bundle.compute()` only READS the sidecar (INVARIANT-06) and with no
receipts the bundle and digest are byte-identical (INVARIANT-08).

**`record_seen(paths, ids, *, via, reader=None, today=None)`** appends one
compact sorted-keys JSONL line for the ids not already receipted on this
machine — lock-free `O_APPEND`, no write lock (L-03), idempotent per id so the
sidecar stays O(engaged ids). `reader` defaults to
`session.detect_session_agent()` and is receipt METADATA for the D-064 matrix
and forensics, never the rendering axis. Open items receipt gameplan-qualified
(`<gid>:O-NN`, numbers restart per gameplan); `cz_check_exit_criterion`
engagement records under the synthetic `criteria:<gid>:<phase>` key,
collision-free with register ids. Symlinked sidecars are refused; every call
site wraps this best-effort — a failed append never breaks the read or resolve
it rides on.

**`load_seen(paths)`** merges the sidecar into
`{id: {first_seen, last_seen, readers, via}}` — torn-line-tolerant (the
telemetry `read_events` convention); a missing or garbled file reads as no
receipts, degrading, never crashing.

**`split_seen(ids, seen, prefix="")`** partitions ids into
`(never_engaged, engaged_but_open)`, order-preserving and exhaustive — every id
lands in exactly one bucket, which is the D-068 assertion the digest goldens
check. `prefix` qualifies the lookup key for open items while the buckets keep
the bare display ids.
