# MYRIAD Ω × UMBRA — v1.9 independently implemented optimization & evidence tribunal

**Date:** 2026-11-23. **Authority:** isolated research-only PR; do not merge to UMBRA `main`, Icarus, or OMNIGENESIS before the original MYRIAD 13/13 gates and owner authorization. No Codex automations, live trades, automatic code merges, or neural model promotions.

## What was actually implemented

Twelve **distinct, executable mathematical black-box optimizers** were implemented without copying third-party project source. They have a common strictly bounded evaluation API, deterministic seeds, numerical input validation, reproducible receipts, and tests. Their names are not claims of unique mathematical invention:

| Method | Defining update mechanism | Reference for mathematical lineage (not copied code) |
|---|---|---|
| Uniform random search | Independent bounded samples | [SciPy optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html) |
| Latin hypercube search | Stratified coordinate permutation | [SciPy quasi-Monte Carlo](https://docs.scipy.org/doc/scipy/reference/stats.qmc.html) |
| Coordinate pattern search | Shrinking coordinate-neighborhood moves | [SciPy optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html) |
| Simulated annealing | Temperature-dependent acceptance of downhill moves | [SciPy dual annealing](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html) |
| Differential evolution | Population difference-vector and binomial crossover | [SciPy DE](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html) |
| Particle swarm | Personal/global attraction and momentum velocities | [DEAP](https://github.com/DEAP/deap) |
| Genetic algorithm | Tournament selection, blend crossover, Gaussian mutation and elitism | [DEAP](https://github.com/DEAP/deap) |
| Cross entropy search | Elite conditional Gaussian refitting | [Nevergrad](https://github.com/facebookresearch/nevergrad) |
| Evolution strategy | `(1+λ)` mutation with adaptive σ | [DEAP](https://github.com/DEAP/deap) |
| Nelder–Mead | Simplex reflection, expansion, contraction and shrink | [SciPy optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html) |
| SPSA ascent | Simultaneous Bernoulli perturbation stochastic gradient | [SciPy optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html) |
| Tabu neighborhood | Novel coordinate proposals with short-term visited-state memory | [Nevergrad](https://github.com/facebookresearch/nevergrad) |

Reference links document method lineage. Each local implementation is new project code, not a downstream install of DEAP, Optuna, SciPy, Nevergrad or proprietary TradingView algorithms. There is no claim that the 250,000 preexisting **parameterized recipes** have become 250,000 distinct implementations.

## Multi-budget evaluation — externally unvalidated synthetic tests

`/mnt/data/MYRIAD_EVOLUTION_V19_1800_TRIAL_SUMMARY.json` and three raw, **private** 600-trial JSON reports are the source receipts for this experiment. Protocol: 12 optimizers × 5 synthetic objective families × 10 seeds × three budgets (64/128/256) = **1,800 actual optimizer trials**. All 12 methods improved their *training* objective median at every budget. **Zero of 12** improved the **independently shifted-target holdout median** at any budget. This is a direct negative finding and the research protocol intentionally does not hide it.

To distinguish overfitting from structural transfer, a separate curriculum repeated 1,800 trials with a **synthetic shared latent target plus seed-specific Gaussian noise**, tested on held-out seed families and separately on unrelated shifted objectives. **12/12** optimizers improved the correlated holdout median; **0/12** improved the unrelated shifted-target median. An invariant synthetic task is easier than an unrelated shift. This result is NOT evidence of learned general intelligence or general market prediction.

- `scripts/evolution_algorithms_v19.py`: twelve independently implemented methods, five synthetic mathematical tests, deterministic multi-budget suite and no implicit system calls.
- `scripts/evolution_transfer_curriculum_v19.py`: explicit correlated vs hard-shift protocol.
- `scripts/evolution_tournament_v19.py`: signed 12-method candidate records consumable by existing **real UMBRA v5 synthetic engine** bridge. Local stub verification is not the release gate; GitHub Actions must run the bridge using the real `engine.mjs`.

## Full-fleet evidence verification (prior v1.8 result, new v1.9 independent checker)

A separate audit examined **all 195,000 recorded synthetic research results** from the v1.8 SQLite evidence ledger in four disjoint ranges: 1–50,000; 50,001–100,000; 100,001–150,000; 150,001–195,000. Zero records failed identity, authority, receipt or mathematical replay checks. **18,402 quarantined candidates** and **176,598 synthetic rejections** were recomputed. All four range-report hashes were independently verified and combined into `research/EVOLUTION_V19_TRIBUNAL_AGGREGATE.json`. The full 324 MiB SQLite source and compressed 69 MB archive remain in the **private** `/MYRIAD-OMEGA/v1.8` ChatGPT Library folder (never public Git).

This tribunal uses the same mathematically defined *synthetic teacher*, but an independent recomputation path; it is reproducibility qualification, **not independent real-world science**. A SHA256 hash by itself does not establish the provenance or authenticity of an externally produced dataset.

`evolution_tribunal_v19.py` also establishes a **cross-domain evidence exchange protocol**: only strictly older, separate-domain, already checksum-verified *quarantined* evidence can be referenced. Recipients receive immutable source receipts and provenance only; their parameters are not automatically applied. Links may propose experiments, never auto-promote weights or write production code.

## Website integration

The read-only Python observatory now serves `/api/methods` for twelve real implementations and `/api/tribunal` for the public aggregate verification receipt. Its animated UI displays methods and confirmed **stored** evidence separately from live running workers. These routes do not grant write access or expose the original neural-bank contents.

## Tests, known blockers and next owners

1. CI must verify the new source manifest, run all v1.8 and v1.9 Python unit tests, and execute twelve v1.9 proposals against actual UMBRA `engine.mjs` on paired seeds. Record the exact current commit SHA.
2. The historic 8.22 GB and 640 MB *trained* weight banks have **not** been recovered. Targets of 30 GB / 10 GB are expansion geometry only; source training receipts and actual full checkpoint bytes remain missing.
3. The 195,000 identities are durable **logical scheduled worker IDs**, not 195,000 live LLM instances. GitHub's hourly diagnostic is disabled by default and processes only a bounded sample if owner-enabled.
4. No authenticated externally hosted website has been deployed. Railway's GitHub account lacks authorization to clone `reppiks490/umbra-sovereign-worlds`. Do not invent a public URL.
5. Before real-world evaluation, add licensed historical datasets, leakage-safe time-splits, causal/null controls, independent holdout sources, workload-cost measurements, authentication, disaster recovery, and explicit operator approvals.
