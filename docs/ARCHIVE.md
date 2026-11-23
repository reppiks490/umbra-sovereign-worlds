# UMBRA Ω — Local world archive protocol (UM-101)

**Status:** feature branch proposal; not yet merged, deployed, independently reviewed, or production validated. This document describes the implementation in archive.mjs and its adversarial tests in tests/archive.test.mjs.

## Why this exists

Before UM-101, a world could be reconstructed from a seed/policy/turn passport, but no independently checked sequence of saved world states existed. A mutable browser state or a self-reported checksum is not a trusted world history. This module introduces **bounded, portable checkpoints** whose content and ordering can be checked against a fresh replay of the deterministic v5 engine.

This is an **in-memory/exportable research artifact**, not a server, durable database, multi-user authority, blockchain, digital signature, or independent witness.

## Contract

- ARCHIVE_SCHEMA is umbra.archive.v1; current ENGINE_VERSION and SOCIETY_VERSION are pinned in each archive header.
- The archive header contains an unsigned 32-bit nonzero seed, the seven policy parameters, and 1–12 checkpoints.
- Each checkpoint contains a strictly increasing tick, the previous checkpoint digest (or GENESIS), a full JSON world snapshot, a SHA-256 digest of canonicalized snapshot bytes, and a SHA-256 digest of {tick,previous,stateDigest}.
- Canonical JSON sorts object keys, preserves array order and numeric precision, and rejects cycles, nonfinite values, unsupported types and excessive nesting.
- Imports are limited to **8,000,000 UTF-8 bytes**; checkpoints are limited to **turn 2,000**. This is a deliberately small local research format.
- On verification, every checkpoint is independently reconstructed from **genesis** using the stored seed and policy, and compared exactly to the saved snapshot. Recomputing a forged checksum is not enough to pass.
- appendCheckpoint is immutable: the input archive is not changed and earlier entries are cloned, not aliased.
- replayFromCheckpoint hydrates a *verified* saved state, advances a bounded number of turns, and cross-checks the result against a separate replay from genesis.
- Import returns nothing until the entire chain is checked. Unknown schema, model version, malformed policy, duplicate tick, chain mismatch and replay divergence are errors.

## Minimal example

Run from a Node 22+ ES-module context or a secure browser context (HTTPS or localhost):

    import {createWorld, advanceWorld} from './engine.mjs';
    import {createArchive, appendCheckpoint, verifyArchive, replayFromCheckpoint,
            exportArchive, importArchive} from './archive.mjs';

    const world = createWorld(49021);
    let archive = await createArchive(world);
    advanceWorld(world, 60);
    archive = await appendCheckpoint(archive, world);
    const exportedJson = await exportArchive(archive);
    // The caller may explicitly download/save exportedJson; this module never writes files.
    const imported = await importArchive(exportedJson);
    const result = await verifyArchive(imported);
    const resumed = await replayFromCheckpoint(imported, {steps:10});
    console.log(result.head, resumed.tick); // SHA-256 hex and turn 70

## Trust model and limits

1. **Tamper detection is not authentication.** Anyone who can rewrite the archive can generate another valid world history from another seed/policy and recompute all hashes. No signature, trusted timestamp, external authority or user identity is established.
2. **Replay is the source of truth.** Imported mutable state is never accepted merely because its digest matches. Engine version changes require a versioned migration/compatibility strategy; this implementation rejects mismatches.
3. **No real persistence yet.** The module provides serializable archive data; it does not call IndexedDB, Supabase, Railway, GitHub, or any network endpoint. Browser download/upload UI is future work.
4. **No real-world validation.** Replay proves consistency with synthetic rules, not empirical truth or policy causality.
5. **Resource budget is explicit.** Verifying a full archive can be CPU-intensive because it reconstructs the world from genesis. The byte, tick and checkpoint limits are intentional denial-of-service controls, not scale claims.
6. **No trusted live-site integration.** The chatgpt.site deployment remains a separate application. Do not deploy this branch or wire production storage without a separately verified host pipeline and review.

## Proof and acceptance

Run npm test (Node 22 in CI). tests/archive.test.mjs checks reproducibility, append immutability, genesis replay, import/export roundtrip, forged digest rejection, broken chains, duplicate/out-of-order ticks, schema/model mismatch, unknown fields, candidate mutation, oversized payloads, checkpoint bounds and invalid horizons.

**Verification status:** Test source added, but results are **unverified until CI or a local test run is observed**. The earlier 31-test v5 baseline does not prove this feature.

## Handoff / provenance

- **Change request:** UM-101 and the owner's instruction to expand UMBRA as far as technically justified.
- **Before:** seeded passport import and deterministic replay, but no chained snapshots.
- **Change:** archive.mjs, tests/archive.test.mjs, this protocol, and knowledge-layer updates.
- **Tradeoff:** exact full-state checkpoints and genesis replay maximize inspectability at the cost of size and replay time. Incremental delta codecs and a remote authority are deferred until evidence justifies them.
- **Compatibility:** no existing engine, society, UI or passport format is modified. Removing the new module restores baseline behavior.
- **Stale when:** engine/society versions, canonicalization, checkpoint limits, archive API, CI matrix or deployment ownership changes.
- **Next owner:** UM-101 implementer may add an explicit browser save/load surface and durable store only after tests and authorization. UM-103 independently reviews the threat model and reproducibility.
