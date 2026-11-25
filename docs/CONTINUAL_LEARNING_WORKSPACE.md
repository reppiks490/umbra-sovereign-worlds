# Continual learning workspace — 2026-11-25

The owner requested substantial and then deeper learning-workspace upgrades. This phase converts the existing per-cycle curriculum into durable owner-local memory and connects the real native LoRA optimizer to evidence-based replay.

## Implemented and exercised

- Transactional SQLite replay bank: experience/learning-workspace/replay.sqlite3. No new dependencies. Full synchronous transactions, foreign keys, 1 GB database cap, 8 GB free disk floor on ingestion. The existing 3 GB total learning allocation is preserved; this is not an extra 1 GB reservation.
- Exact prompt SHA-256 identity, permanent cross-cycle and cross-family train/retention/transfer assignment, conflicting answer/options rejected atomically, idempotent per-family snapshots. Exact-text identity does not detect semantic near-duplicates.
- Fixed eight retention and eight transfer anchor examples per family, stored immutably at first successful ingestion and reused across later curricula. Rotating holdouts supplement fixed anchors within a 32-example per-split limit.
- Exposure-aware balanced replay selects distinct underused examples across domains from a bounded 512-candidate pool. Family-level exposure history only; 4096 individual agent weights are not trained by this.
- Actual optimizer consumes replay-selected rows, records question hashes, selected domains, training steps and before/after per-domain answer-only negative log-likelihood. Fixed-anchor metrics are derived from the same evaluation pass, avoiding duplicate model forwards.
- Promotion requires both original retention/transfer gate and fixed-anchor non-regression within 0.02 NLL. Accepted adapters remain staged until transactional evaluation evidence is recorded; only then is the active pointer replaced. Existing base checkpoints are preserved. An accepted evaluation is not proof that pointer activation succeeded if the subsequent filesystem write fails.
- Durable evaluated-attempt IDs, immutable evidence, idempotent replay exposure accounting and provenance. Only completed evaluated optimizer attempts increment exposures; interrupted steps are not captured by this version. No model truth or inference claims based solely on data ingestion.
- Existing INFINITY service refreshes replay bank after the full curriculum pipeline succeeds; native training defers if replay preparation fails. No new scheduler or download interference.

## Live result

Two real local curriculum snapshots ingested: 364 model-specific rows, 182 unique prompts, 126 training / 28 retention / 28 transfer unique prompts, 41 domains, 32 family-specific fixed anchor assignments. SQLite file 397312 bytes. Actual read-only replay rehearsal selected 16 distinct training prompts from 16 domains per family (32 selections total); no model execution, optimizer exposures or fabricated training attempts were recorded. At verification, attempts=0, accepted_attempts=0, evaluations=0, exposures=0. Actual native optimizer awaits verified training runtime/checkpoints and RAM admission. Fixed anchor tests and synthetic curricula are not general intelligence validation.

Seven learning workspace, four native LoRA, fourteen INFINITY Python and 189 Node tests passed (214 across rerun suites). Tests cover cross-cycle contamination, cross-family split conflict, balanced replay, idempotent attempt accounting, fixed anchor stability, promotion regression and nonfinite losses. Full native model execution not yet tested.

Next: per-example outcome-driven difficulty (not just exposure), semantic duplicate screening, independent externally sourced holdouts, durable interrupted-step receipts and per-agent specialization, neural teacher inference and calibrated comparisons. Keep the existing model acquisition queue and SSD protections in place. Latest observed six verified neural bundles (6.80 GB), SmolLM2-1.7B transfer active, ~21.90 GB disk free. No downloads interrupted, storage allocation unchanged.
