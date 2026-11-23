# UMBRA Ω — Pre-registered synthetic experiment tournament (UM-103)

**Status:** proposed feature branch, not merged or deployed. Code: `research.mjs`; verification: `tests/research.test.mjs`. This work belongs to the existing Reality Court/science track (#3), but does not change `court.mjs` or `engine.mjs`.

## The decision this enforces

Experiments must be specified **before outcomes are inspected**, with a fixed engine version, two fully declared seven-axis policy vectors, outcome measure, turn count, master seed, number of replicates and partition. Selective reporting after watching a favorite scenario cannot be presented as pre-registration.

The manifest `umbra.research.v1` embeds derived seed IDs and an explicit 75% exploration / 25% confirmation split. **These are two partitions of generated synthetic model runs**, not a train/test split on empirical data, an external sample, or a demonstration of predictive power.

- `defineResearchPlan()`: creates a serializable manifest. Bounds: 20–64 independent replicate seeds; 1–240 turns; unsigned 32-bit nonzero master seed; only supported outcomes.
- `validateResearchPlan()`: checks exact manifest shape, engine, policy values, seed derivation and frozen split, rejecting modified seeds and unfamiliar fields. It does not sign the plan or prove a human preregistered it earlier.
- `evaluateResearchPlan()`: executes matched-seed baseline and intervention worlds, plus an **identical-policy negative-control world for every replicate**; checks exact deterministic same-policy replay, finite resources, regional population reconciliation and civic transfer conservation.
- Output: complete per-seed raw outcomes and signed differences, exploration and confirmation mean/median/5th/95th **sample percentiles**, counts above/below zero; no p-values or implied real-world confidence bounds.
- Explicit BLOCKED statuses remain for external calibration, prediction and real-world causal validity.

## API example

    import {defineResearchPlan,evaluateResearchPlan} from './research.mjs';
    import {DEFAULT_POLICY} from './engine.mjs';

    const plan=defineResearchPlan({
      seed:49021,trials:24,steps:90,outcome:'population',
      baseline:DEFAULT_POLICY,treatment:{...DEFAULT_POLICY,trade:0}
    });
    // Save the manifest yourself before inspecting or publishing the results.
    const result=evaluateResearchPlan(plan);
    console.log(result.exploration,result.confirmation,result.checks);

The module performs no filesystem, network, cloud, database, brokerage, personal finance, or deployed-site operations. The caller owns any later storage or publishing. No other module imports `research.mjs` yet; there is no new UI.

## Verification and falsification

Run `node --test tests/research.test.mjs` or `node --test tests/*.test.mjs`. Tests include fixed plan/seed derivation, 20–64 runs, identical-policy zero-effect controls, deterministic full reports, tampered manifest rejection, parameter bounds, outcome channels, and intentionally corrupted population/civic state. **As introduced, source and test cases are not evidence of passing CI; attach an observed run and commit below.**

## Limits and trade-offs

1. The original engine remains a **synthetic aggregate model**, not a validated agent-based representation of real residents or ecological systems.
2. Confirmation replicates come from the **same simulation rules** as exploration; they are not independent empirical evidence. A correct but unrealistic model can pass every internal check.
3. The prespecified plan is not cryptographically signed or externally timestamped. An editor can create a new valid plan after seeing results; real scientific preregistration needs third-party attestation and process controls.
4. Negative controls and balanced ledgers are powerful *engineering checks*, not external scientific validity.
5. This first tournament compares **two policies inside one rule engine**; it does not implement multiple independent world simulators or statistical/ABM model baselines. The word *tournament* describes a reproducible experimental protocol, not a finished multi-model competition.
6. Larger factorial/global-sensitivity studies, licensed calibration data, proper scoring rules, server archives and public leaderboards remain future work, each with separate acceptance gates.
7. Computation runs on the calling thread; do not wire the synchronous evaluation directly into animation frames. Use an explicit worker with cancellation and performance budgets if a future UI integrates it.

## Knowledge delta and handoff

- **Why:** #3 requires adversarial falsification and fixed multi-seed experiments before describing synthetic stories as science.
- **Before:** `pairedExperiment()` provided fixed-seed comparisons and `runCourt()` checked a single world, but there was no separately validated predeclared seed partition, strict manifest or per-replicate null control.
- **After proposal:** the additional opt-in manifest and evaluation API provides those constraints without changing engine semantics.
- **Rejected alternative:** automatic post-hoc optimization on the highest-scoring seed; that would manufacture biased narratives.
- **Backward compatibility:** imports are opt-in; removing `research.mjs` and its tests restores the previous v5 runtime.
- **New rules:** no real-world calibration/forecast/causality PASS unless independently sourced, licensed and verified; do not execute this CPU-bound method in the render loop.
- **Verification status:** CI result pending; tests not executed locally.
- **Stale when:** `ENGINE_VERSION`, supported outcome metrics, seed derivation, plan schema, execution cost or CI evidence changes.
- **Next worker:** run CI; independently audit code and output semantics; then integrate a cancellable worker only after review and quantitative profiling.
