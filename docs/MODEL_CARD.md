# Model card — UMBRA Sovereign Worlds 4.0.0

Status: **synthetic educational/artistic simulation**. This document follows the broad purpose/schedule/assumptions/evaluation distinctions of Grimm et al.'s 2020 ODD modeling protocol. **This is NOT a validated agent-based population model.**

## Purpose and domain

Explore *within-model* feedback between synthetic settlement growth, resource scarcity, food exchange, disease, technical knowledge, conflict, and environmental stress. Users can create hypothetical forks, compare seeded histories and inspect simulation effects. The domain is deliberately fictional. Nothing in the code is fitted to a real census, climate, epidemiological or economic dataset.

## Entities and scale

- **World**: a deterministic set of 42 fixed synthetic geographic regions, arranged by a Fibonacci sphere. Six nearest spherical neighbors are precomputed per region.
- **Settlement**: an aggregated state record (population, food, water, energy, knowledge, wealth, illness, stress, health, lineage generation, culture group, drought trait). No individual persons or households exist.
- **World**: totals, climate state, trade events, provenance parameters, and bounded history.
- **Events**: synthetic changes caused by the model rules; they are not observed external events.

At genesis, ten seed colonies are established with a fixed initial stock. Other regions begin uninhabited. The program advances one synthetic time step per update; steps are **not equivalent to physical days, years, or real-world time**. The animation's speed has no external historical meaning.

## Schedule and mechanics

Each turn `stepWorld`:

1. Computes deterministic seasonal weather and shock center from world seed and turn.
2. Iterates inhabited settlements; updates food, water and energy after consumption, resource production, climate loss, and endogenous knowledge.
3. Updates sickness, shortages, births and losses through explicit heuristic formulas.
4. Applies threshold-driven migrations and founding, inheriting some attributes from parent colonies.
5. Moves food from nearby surplus settlements to deficit settlements when trade is enabled.
6. Diffuses technology to adjacent colonies; updates carbon/biodiversity and generates chronicle events.
7. Aggregates state; records a bounded time-series and sparse snapshots.

`engine.mjs` is the authoritative specification. All parameters are **hand-selected**, not calibrated, and the apparent variable meanings (medicine, climate, etc.) are analogies, not physical dimensional measures. Measurements like "residents" in this simulation can be fractional internally and are rounded only for display; they should not be interpreted as counts of real individuals. Some rules impose synthetic ceilings and approximations, e.g. maximum resources per region and capped population. The disease process does not implement real-world compartmental epidemiology. The wealth and emissions measures have no empirical units.

## Inputs and provenance

`createWorld(seed,policy)` receives a 32-bit positive seed and the seven policy values, each clamped to `[0,1]`:

| Parameter | Rule family influenced |
| --- | --- |
| trade | Transfer volume between food-surplus and food-deficit neighboring regions |
| climate | Harvest, stress and disaster pressures |
| medicine | Illness generation and recovery |
| innovation | Knowledge gain and diffusion |
| migration | Movement rate under shortages |
| conservation | Carbon pressure and biodiversity adjustments |
| conflict | Population loss and knowledge drag under stress |

`noise(seed,tick,site,channel)` uses integer hashing rather than global mutable random state. Identical seed, version, rules, and step count reproduce the same state. **Independence of environmental random draws from policy does not guarantee the endogenous behavior of the worlds is identical:** that divergence is precisely the measured simulated effect.

## Experiment design

`pairedExperiment` generates 2–64 paired trials (up to 2,000 turns each). It uses one derived seed for each pair, and both worlds share that seed. The baseline is default policy; the treatment is chosen from the forge slider positions. It records the final *baseline minus treatment* population difference, mean, median, 5th/95th empirical sample percentiles, sample standard deviation, count of positive outcomes and every paired run's seed/totals. Unlike a simple single-world comparison, this evaluates how a rule perturbation behaves across several initialized simulated worlds.

**Interpretation constraint:** No randomized real-world trial, no validated causal graph, no observational calibration, no pre-registered external target, and no field data. Paired-seed results are model-conditional; sample percentiles do not give policy-effect confidence bounds for actual populations.

## Reproducibility and verification

- `node --test tests/engine.test.mjs`: deterministic same-seed replay, split stepping, exogenous shocks across policies, zero-effect same policy, 42 unique region names, bounds, long stress, passport input checks.
- `python tests/smoke.py`: browser behavior at three viewports, chart/controls and JavaScript errors; uses inline browser assembly in restricted environment.
- `buildPassport`: seed, version, policy, turn, totals, bounded history, optional experiment statistics, creation timestamp and assumptions. Export includes an optional locally computed SHA-256 hash over the pre-checksum JSON payload; import verifies it in secure contexts when present. No certificate, private signing key, timestamp authority, or independent witness exists. If a checksum is absent, source authenticity is unverified.

### Validation maturity

- **Engineering invariants / deterministic reproducibility:** testable and verified in this packaged build.
- **Numerical coherence and sensitivity:** only elementary invariants and limited stress checks; no comprehensive parameter identifiability analysis.
- **Scientific validation:** **NOT PERFORMED**. No calibrated dynamics, real-world forecast skill, empirical targets, or independent replication.
- **Ethical legitimacy for real policy use:** **NOT ESTABLISHED**.

## Known model limitations

1. Fixed regions and a heuristic sparse-neighbor network; no road or travel-time geometry.
2. No individual cognition, families, religion, language, class or politics; emergent narratives are synthetic event templates.
3. No energy technology lifecycle, trophic ecology, real environmental feedback cycles, immigration borders or institutional incentives.
4. Dynamics can saturate heuristic resource thresholds; avoid mistaking model equilibrium for empirical universal law.
5. Trade flows are one-step local resource transfers, not endogenous currency prices or a real market with order books.
6. Carbon is a synthetic counter, not atmospheric CO₂; biodiversity is a synthetic bounded index.
7. No persistent cross-device shared state; browser refresh resets the simulation unless a passport is imported.
8. No audited source licenses or external data pipelines because no external data is ingested.
9. The product uses a CPU canvas visualization; no 3D physics engine or GPU-backed simulation.
10. No deployment, external site modification or background agents are part of this package.

## References

- Grimm et al. (2020). [The ODD protocol: second update](https://www.jasss.org/23/2/7.html). DOI 10.18564/jasss.4259.
- NetLogo (current manual). [BehaviorSpace](https://docs.netlogo.org/behaviorspace) — reproducible computational experiments and repeatable seeds. UMBRA does not embed NetLogo.

### Replay evidence boundary
The exact-replay CLI compares complete independently executed engine states in addition to its legacy selected metric digests. It does not change simulation rules, validate real-world causality, or confer production authority.
