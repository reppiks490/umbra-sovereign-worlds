# Evidence and implementation audit

## Origin inspection — November 22, 2026

User-provided URL: https://umbra-focus-orbit.orange-cake-1541.chatgpt.site/

Site inspected read-only with Firecrawl and Parallel extractors, plus inspection of publicly served JavaScript modules using a remote read-only browser. Public page title: **Umbra · The Living World**. Observable UI: animated orbital world view, selected settlement telemetry, story dispatch, trade vs no-trade paired world counts, world chronicle. Live code referenced `broadcast.mjs`, `ecology.mjs`, `planet.mjs` and `motion.mjs`.

The live `broadcast.mjs` constructs `newWorld(era)` and a no-trade twin, advances each to `atTime(Date.now())`, and renders an HTML/canvas interface. The live `ecology.mjs` implements deterministic regional populations, food, founding, migrations, and trade shocks. It does not establish a remote persistent agent service. The live page's “On air” means the page is advancing, not proof of server-side agents.

**Site operation not changed.** The origin repository was not identified through the connected GitHub repository search. The previously connected `EPOCH Ω` repository is an unrelated project and was not overwritten. The `chatgpt.site` publishing endpoint is not available for authorized edits through our current connected tools.

## v4 output provenance

Created independently as a new static ES-module app in `UMBRA_SOVEREIGN_WORLDS_v4/`. The original UI's broad visual themes and synthetic civilization concepts are contextual references. v4 code is standalone, dependency-free code with newly defined rules and structures. v4 is **not a verified 1:1 upgrade of the original site's engine**, and its metrics should not be numerically compared against original live metrics as though they are the same model.

## Verification record

Executed locally:

- `node --test tests/engine.test.mjs`: **12 tests passed, 0 failed**.
- `python tests/smoke.py`: **3 viewport smoke checks passed** (1440×900, 390×844, 768×1024), zero Playwright page exceptions, zero horizontal overflow. Tests exercise step, controls, regional selection and a deterministic paired experiment.
- Visual full-page browser screenshots inspected manually for layout and readability; screenshot artifacts are available separately, not necessary for running the app.

Limitations of verification: scripts are served inline in the browser smoke test due local sandbox navigation restrictions. Actual deployment to a public host, hosted module resolution, iOS Safari device tests, worker behavior on an external host, real accessibility audit and performance benchmarks on user hardware **have not** been verified. Do not claim otherwise.

## Permission / account boundaries

No financial account, broker, wallet or private files used. No source keys accessed. No trades, API writes, paid model tasks, or changes to the user-provided `chatgpt.site` project. No GitHub source writes performed for UMBRA in this release. MagicPath external-agent quota was exhausted and not bypassed. No claims of multiple independent coding agents executing when they did not.


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


### Continual learning workspace
See [CONTINUAL_LEARNING_WORKSPACE](CONTINUAL_LEARNING_WORKSPACE.md) for transactional replay memory, persistent split protection, fixed assessment anchors, exposure-aware native optimizer replay and durable learning evidence. Actual weight updates remain pending runtime and memory admission.


### EXASOVEREIGN pre-December 18 campaign (2026-11-25)
See docs/EXASOVEREIGN_PRE_DEC18_CAMPAIGN.md for the owner-approved 28 GB neural-first + 15 GB resource queue, storage and license gates, proposed milestone criteria and explicit unverified status. Resource acquisition is data-only, not training or deployment.


EXASOVEREIGN campaign update: six executable deterministic numerical lanes and balanced, license-screened resource qualification; see docs/EXASOVEREIGN_PRE_DEC18_CAMPAIGN.md. Synthetic baseline verification is not neural inference or training.
