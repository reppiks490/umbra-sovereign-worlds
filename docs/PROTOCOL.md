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


## E: Independent placebo replay in the advanced CLI lab (UM-111)

The former placebo-falsification case compared two reads of the same cached world. That is not independent replay. The corrected case calls the simulator twice without using its cache, applies identical tick, settlement, civic and finite-metric checks, compares complete state digests and deep equality, and rejects reused object identity or divergence. The evidence includes both full-state digests and the two actual executions. The existing sample digest remains for comparison.

`uniqueWorldStates` counts distinct seed/horizon/policy keys, while `simulationExecutions` counts actual full simulate() calls through the advanced-lab runner, including fresh exact replay; separately chunked advancement is not a full simulate() call. A placebo run should report one key and two executions. Existing evidence from before this fix cannot establish independent placebo reproduction. This is an engineering reproducibility control within the synthetic engine, not independent empirical validation.

Verification: isolated helper RED missing module, GREEN four Node tests including divergent output, invalid second run, cache accounting and shared object rejection. Exact source hashes match the tested local bytes. A registered U1101 CLI test has been added; full repository and exact-head CI evidence are pending. No simulation-rule changes, external data, deployment, or production authority.

### Exact-replay extension (UM-111 follow-up)
Exact-replay now shares the existing `independentReplay` mechanism with placebo-falsification: two fresh validated simulations, full-state SHA-256 digests, object independence and deep equality. Legacy sample digests remain available. A fault injected into an unsampled state field was accepted by the original CLI but rejected by the corrected CLI. The new receipt fields are additive; older receipts do not prove full-state equality.
