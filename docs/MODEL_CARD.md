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


### AUTOGENESIS Ω (bounded synthetic learning)
See [AUTOGENESIS documentation](AUTOGENESIS.md). Adds 100 strategy-role configurations, paired-seed exploration, learned numerical reward prediction, disjoint holdout promotion, checkpoint integrity and bounded owner-local endpoints. No independent trained agent fleet, native-model training, deployment or scientific qualification is implied.


### Agentic Nexus Ω
See [Agentic Nexus](AGENTIC_NEXUS.md) for the owner-local council, native BERT inference, experience bank, replay-verified training and adaptive model routing. Synthetic evaluation only; native pretrained inference and broad agentic capability remain unqualified.


### Hugging Face-backed weight cache
See [HF weight cache](HF_WEIGHT_CACHE.md): owner-only eviction and checksum-pinned restoration of original public single-file native weights, remote registry and opt-in supported-model retrieval. No automatic deletion, private uploads or Ollama weight eviction.


### UMBRA INFINITY Ω
See [INFINITY](INFINITY.md) for the autonomous public model discovery, bounded retrieval qualification, managed-cache rotation, local scheduling and current limitations.


### Intelligence gap detection and consolidated handoff
See [Gap detection](GAP_DETECTION.md) and [Master handoff](MASTER_HANDOFF_20261124.md) for evidence-driven capability assessment, benchmarked local models, deterministic fallbacks, discovery prioritization, automatic audit scheduling, and remaining qualification work. No broad intelligence or production qualification is asserted.


### MEGASWARM Ω and native training
See [MEGASWARM](MEGASWARM.md) for the 4,096 shared-weight agent population, verified cross-model teaching, numerical learning and research, native training bootstrap, autonomous scheduling, pilot LoRA gates, evidence and unresolved limitations. Logical agents are not independent trained weight copies; native fine-tuning remains unverified pending download and RAM admission.


### Progressive swarm academy
See [SWARM_ACADEMY](SWARM_ACADEMY.md) for ten-tier verified task generation, student-to-teacher lineage, the fixed 7B reference target, native adaptive LoRA growth, resource limits, and remaining qualification work.


### Market Academy Ω
See [MARKET_ACADEMY](MARKET_ACADEMY.md) for 24 market lanes, ten tiers, source-reviewed mechanism questions, verified teaching/evaluation separation, native corpus expansion and empirical market-data roadmap. No trading authority or demonstrated market prediction ability.


### OMNISCIENCE knowledge and session recovery
See [OMNISCIENCE](OMNISCIENCE.md) for the six-division curriculum and pinned, disabled external capability registry, and [session recovery ledger](SESSION_RECOVERY_LEDGER_20261125.md) for the recoverable requests, verified work, constraints and outstanding tasks.


### Local repository fabric
See [LOCAL_REPOSITORY_FABRIC](LOCAL_REPOSITORY_FABRIC.md) for the mounted-drive and WSL discovery, existing MYRIAD manifest reconciliation, shared source registry, verified agent inheritance and post-acquisition qualification gates. Local source availability is not executable integration.


### Verified repository execution and learning
See [REPOSITORY_EXECUTION_LEARNING](REPOSITORY_EXECUTION_LEARNING.md) for five real pinned numerical adapters, source browsing, six replayed repository lessons, complete corpus audit, scheduler readiness gate, download recovery and remaining qualification work. This does not certify whole-package execution or trained LLM weights.


### Acquisition recovery
See [ACQUISITION_RECOVERY](ACQUISITION_RECOVERY.md) for the resumed Q8 and neural/tiny queue, automated retries, reuse of installed CPU PyTorch, storage admission and actual outstanding downloads.


### Neural priority expansion
See [NEURAL_PRIORITY_EXPANSION](NEURAL_PRIORITY_EXPANSION.md) for the 15 GB native-weight cap, complementary model ranking, resumable supplemental queue and storage safeguards.
