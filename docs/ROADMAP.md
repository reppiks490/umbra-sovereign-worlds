# UMBRA Ω — The far-horizon expansion map

This is a **research and engineering roadmap, not a feature list of the current build**. Deliverables require explicit acceptance gates. Ambition is measured by depth, correct interactions, and proof—not by decorative module counts or unbounded agent claims.

## Constellation I — Real persistence and temporal truth

| ID | Research/engineering objective | Proof gate |
| --- | --- | --- |
| P01 | Persistent world identities and append-only turn event logs | Process restart returns exactly the same versioned state |
| P02 | Shared multi-user real-time world subscriptions | Two devices render the same authoritative state under disconnections/reconnects |
| P03 | Model-version migration and tamper-evident event ledger | Old runs replay by frozen engine version; ledger mutations detected |
| P04 | As-of data / bitemporal source provenance | Correct view given observation time and capture time; corrections preserve history |
| P05 | Fork trees with bounded snapshots and causality edges | Deterministic branch lineage and replay across forks |

## Constellation II — Persons, genetics, cognition and culture

| ID | Objective | Proof gate |
| --- | --- | --- |
| A01 | Individual birth/death, households, roles and social networks | Conservation and inheritance invariants under randomized stress |
| A02 | Genetic traits, mutation, trade-offs and selection | Multi-generational distributions against analytic baselines |
| A03 | Language, norms, conflict/alliances and cultural transmission | Model-level experiments show measurable falsifiable hypotheses |
| A04 | Memory-limited goal-seeking citizens, not scripted omniscience | Task success and failure against deterministic non-LLM baselines |
| A05 | Interacting institutions, laws, legitimacy and elections | Transparent state transitions, adversarial manipulation tests |
| A06 | Migration, diaspora, family lineage and cross-border exchange | Reproducible migration ledger and diversity measurements |
| A07 | Separating simulated "intelligence" from fictional anthropomorphism | Model card and predeclared behavioral criteria; no consciousness claims |

## Constellation III — Planetary ecology

| ID | Objective | Proof gate |
| --- | --- | --- |
| E01 | Spatial climate and hydrology, wind belts and ocean currents | Numeric stability, mass/energy budgets, documented scale units |
| E02 | Food webs, biomass, habitats, species adaptation and extinction | Trophic and conservation invariants, sensitivity ranges |
| E03 | Resource geology, minerals and industrial supply chains | Stock-flow accounting through production networks |
| E04 | Wildfires, epidemics and extreme climate stress | Calibrated or overtly synthetic scenario benchmarks |
| E05 | Land-use change, pollution, restoration and tipping points | External replication, clear uncertainty boundaries |

## Constellation IV — Markets, economies and technology

| ID | Objective | Proof gate |
| --- | --- | --- |
| M01 | Endogenous currencies, banks, debt and trade contracts | Double-entry invariants and deterministic transaction replay |
| M02 | Production input-output networks and supply shocks | Accounting-balanced commodity flows; independent shock tests |
| M03 | Fiscal policy, taxation, public goods and inequality | Reconciliation of transfers, population-level distributional effects |
| M04 | Price discovery and limit-order microstructure | Price-time priority, latency, costs and external benchmark when claimed |
| M05 | Technology diffusion, R&D investment and dynamic comparative advantage | Long-run growth modeled with controls and uncertainty reporting |
| M06 | Strict segregation from real capital | Paper-only research permissions; explicit deny-by-default live execution |

## Constellation V — Simulation science and robustness

| ID | Objective | Proof gate |
| --- | --- | --- |
| S01 | ODD-complete scientific specification | Independent reimplementation is unambiguous |
| S02 | Seed grid, full factorial and global sensitivity studies | All seed/parameter/horizon inputs and summary stats archived |
| S03 | Intervention semantics and causal diagrams | Identifiability assumptions exposed; observational claims blocked |
| S04 | Particle/Bayesian inference if calibration data is licensed | Posterior predictive checks and held-out validation |
| S05 | Model competition against null, statistical and ABM baselines | Prespecified proper scoring and temporal splits |
| S06 | Adaptive experiment selection with guardrails | Reproducible evaluation, no p-hacking to a favorite scenario |
| S07 | Independent red-team testing for drift and adversarial inputs | Bounded tests with observed failures, not invented pass badges |

## Constellation VI — World-scale visual and cinematic rendering

| ID | Objective | Proof gate |
| --- | --- | --- |
| V01 | GPU-first scalable renderer with cinematic globe and terrain LOD | Measured p50/p95 frame times at desktop and iPhone targets |
| V02 | Terrain, weather volumes, orbit cameras and streaming cities | Stable, coherent motion beyond additive fin/tail-only effects |
| V03 | Flow-field populations and agent embodiment | Character/world motion synchronized with simulated decisions |
| V04 | Deterministic temporal cinema exporter | Scrub, record, export and compare resulting frames and timestamps |
| V05 | Directional soundscapes, adaptive music, accessibility captions | A/V synchronization, mute, hearing accessibility tests |
| V06 | Motion design, interactive maps, layered cinematic reporting | Keyboard/touch targets, reduced motion, visual diff regression suite |

## Constellation VII — Operational autonomy with boundaries

| ID | Objective | Proof gate |
| --- | --- | --- |
| O01 | Agent research planners with bounded, auditable roles | Explicit permissions, provenance and no unauthorized actions |
| O02 | Parallel scientific tasks and coordinated branch ownership | Collisions prevented and reproducible integration tests |
| O03 | Observability, error budgets, performance budgets and monitors | Live trace/metric checks with provenance and incident history |
| O04 | Provider adapters for scientific and licensed public market data | Contract, rate-limit, timestamp and usage-rights checks |
| O05 | Cloud compute/scheduling and durable crash recovery | Resume tests after simulated outage and verified hosted runs |
| O06 | Experimental public API and connector gateway | Versioned contracts, authorization, secrets, audit events |

## Constellation VIII — Creative universe and value

| ID | Objective | Proof gate |
| --- | --- | --- |
| C01 | Guided experiments and educator/investigator scenario packs | Blind usability tests and reproducible lesson outputs |
| C02 | Multi-world storytelling with provenance-aware narrators | Stories link exactly to events and never fabricate histories |
| C03 | Time-lapse documentaries and creator exports | Export rights, subtitle and rendering fidelity tests |
| C04 | Community open simulation challenges and peer review | Reproducibility and good-faith benchmark moderation |
| C05 | Legitimate monetization options: hosted worlds, education, creator tools | Value experiments; no guaranteed profit assertions |

## Plugin architecture, intentionally selective

Potential integrations mentioned by the owner (NOT activated by this package): GitHub/Codex Coordinator/Baton Pass/Akinator/Trellis/Linear for code workflow and structured knowledge; Supabase/Railway for persistence and deployment; Figma/MagicPath/MotionDesign/Runway/Hypernatural/PINOC/Voyager 3D/FFmpeg for design, motion, and production; NVIDIA/Hugging Face/Scite/Parallel/Exa/Tavily/Firecrawl for licensed AI/research pipelines; FMP/Massive/TickerLayer/Unusual Whales/CoinGecko and other finance feeds only if a later, clearly separate, permissioned economic simulation requires them. Personal Finances should **not** be used by default to build a fictional civilization. Avoid calls to all connected apps merely to inflate a feature count.

**Major gating distinction:** Public evidence can inform scenario assumptions, but it does not automatically validate simulation equations or produce causal identification. The user must separately authorize account access, new costs, external writes, hosted deployment, real-world data, and trading. The current v4 is intentionally local-only.


### AUTOGENESIS Ω (bounded synthetic learning)
See [AUTOGENESIS documentation](AUTOGENESIS.md). Adds 100 strategy-role configurations, paired-seed exploration, learned numerical reward prediction, disjoint holdout promotion, checkpoint integrity and bounded owner-local endpoints. No independent trained agent fleet, native-model training, deployment or scientific qualification is implied.
