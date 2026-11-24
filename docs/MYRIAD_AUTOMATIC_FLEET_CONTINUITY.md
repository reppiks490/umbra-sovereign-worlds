# Automatic fleet continuity — 2026-11-24
The recurring default-branch orchestrator selects only an earlier successful run
with all fifteen nonexpired group artifacts, checks the exact pinned engine source,
logical hour, group, per-shard SHA-256, identity set, authority and per-receipt digest,
then hydrates the previous synthetic records into the current shard ledger.
The existing engine requalifies prior candidates; the orchestrator binds every
claimed peer parent to its actual recovered record. If no suitable prior run exists,
the cycle is explicitly labeled bootstrap. Corrupt admitted evidence fails closed.
Artifacts are retained two days; this is bounded recent continuity, not a permanent
archive, authenticated scientific provenance, neural learning or full model-worker fleet.
Existing manual entries do not need to be clicked; scheduled batches cover the cases.
The original 300-case lab and v3.3 native model tests are included in twice-daily
qualification; no model inference is performed in public CI.
