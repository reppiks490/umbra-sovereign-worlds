# Experimental protocol — v4

**Aim:** assess rule behavior within the synthetic UMBRA engine, and prevent claims that confuse simulation outputs with external facts.

## A: Reproducible paired comparison

Fix engine version, baseline/treatment vectors, number of seeds, turn horizon, and outcome measure before running. Run the same seed on both sides of each pair; use independent derived seeds across pairs. Report mean, standard deviation, sample percentiles, number of positive differences and all run records. Retain zero-effect baseline test with identical policies as a control. If a rule impacts an output indirectly, annotate that coupling rather than ascribing a validated causal mechanism.

## B: Sensitivity investigation (not yet automated)

Vary each of the seven parameters in predeclared increments, then use a small factorial grid of important interactions. Report sign flips across seed sets and nonlinear thresholds. Include time horizon variation, tail outcomes and catastrophic failures. Resist optimizing a particular seed to produce a preferred story. The current UI runs one paired treatment vector per experiment; full sweeps remain a future phase.

## C: Credibility gates (unmet for real-world policy use)

1. Independent benchmark data and permitted licensing.
2. Clear mapping between synthetic variables and real-world measurement units.
3. Calibrated parameters on a training sample and an untouched temporal validation sample.
4. Out-of-sample predictive comparisons against a no-skill baseline.
5. Explicit causal assumptions and tests of identification/nonidentification.
6. Sensitivity to initialization, seeds, timescale, and plausible alternative rule sets.
7. External independent audit/reproduction.

**Any unmet gate forbids treating outputs as real-world forecasts or policy effects.**

## D: Audit record

Exports contain seed, engine version, policy, generated data/assumptions, and optional experiment. The optional SHA-256 value only checks local file integrity and is not a signature or externally witnessed proof. The model engine is authoritative and recomputes state on import rather than trusting a snapshot of arbitrary serialized state.

## UM-106 replay-bound integration — 2026-11-26

Before independent replay, reject invalid caller budgets and malformed turn metadata; cap each replay to the engine's 5,000-turn maximum. A blocked result is missing evidence, never a pass. Preserve prior seeded semantics.

## UM-106 corridor and PR verification - 2026-11-27

Reject negative and out-of-range corridor endpoints at civic audit and G06 even when replay is blocked. PR qualification invokes core verification with read-only permissions; preserve existing schedules and bounds.

## Workflow catalog namespace correction - 2026-11-27

Three-digit U001-U300 workflow namespace is audited separately from the four-digit advanced namespace. Retain independent validation of both catalogs.
