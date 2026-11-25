# Engineering continuation handoff

## Present deliverable

New standalone web prototype **UMBRA Ω Sovereign Worlds v4**. Entry: `index.html`, source: `engine.mjs`, `observatory.mjs`, `lab.worker.mjs`, `world.css`. The experiments are deterministic synthetic *regional* models. No local/remote backend and no persistent autonomous agents. Tests and run instructions in README.

## Separately identified projects

- Original live `https://umbra-focus-orbit.orange-cake-1541.chatgpt.site/` is an *existing, separate* civilization experience. We inspected its published sources but could not identify/edit its origin/deployment.
- `reppiks490/all-of-the-build-as-they-are-as-of-2-13am-9-26-2026` has **EPOCH Ω v3** source. Preserve it. Don't copy UMBRA over EPOCH without user authorization.

## Next iteration priorities

**First:** obtain official UMBRA source repository and site deployment pipeline; run a baseline snapshot before integrating, make a change branch, protect original history, and verify tests/diff. No force pushes.

**Second:** separate engine simulation and renderer with a proper hosted ESM build/instrumentation; use browser hardware tests, control CPU/GPU budget, avoid misleading FPS targets.

**Third:** pursue research gates in `docs/ROADMAP.md`, starting with true append-only world persistence, bitemporal event provenance, empirical calibration if intended for scientific claims, and agent-based person-level models only with explicit design and independent verification.

**Fourth:** add content accessibility and keyboard navigability, testing with mobile Safari / WebKit, a worker runtime test on a real HTTP host, and benchmark registration. Archive experimental seeds before changing rules.

## Tested acceptance

Engine tests 12/12 pass. Three browser-size smoke checks pass under inline test harness. Source import with secure browser context and production network hosting remain untested. No live site changes/deploys. Model fidelity not validated.

## Stop / release criteria

Never claim a branch/PR/merge/hosting release exists without checking provider responses. All published claims must map to code and test evidence; mobile appearance is not a performance guarantee. Keep financial integrations opt-in and sandbox-only until a separate mandate and compliance controls. See `AGENTS.md` for guardrails.

## 2026-11-24 owner-local continuation

Native compute PR #26 provides the actual engine-backed stdio tools. The stacked owner-local branch adds `mcp/owner_once.mjs`, a one-request local execution path for an independently authorized Desktop Commander connection; see `docs/UMBRA_OWNER_LOCAL_EXECUTION.md`. No public endpoint, model training, or production deployment is implied. Keep MYRIAD PR #21 separate and preserve existing schedules. Require exact-head tests and owner-machine receipts before claiming operational readiness.

## Owner-local model adapters

See `docs/UMBRA_LOCAL_MODEL_ADAPTERS.md`. The owner CLI now routes explicit model_list and model operations to installed Ollama models for bounded synthetic evidence commentary or retrieval fingerprints. Runtime adapters are not trained LoRA weights; no automatic training or live engine decisions. Preserve the separate research and inventory PRs and verify exact-head tests before merging.

## POLYMIND continuation

See `docs/UMBRA_POLYMIND.md`. The multi-source acquisition and owner-local unified dispatch branches extend #29/#30. Model discovery and one-request execution use existing Ollama or a separately configured ONNX Python environment; engine state is unchanged. Verify exact revision and actual owner catalog before inference. Preserve the disk reserve, distinguish download from inference qualification, and do not treat the catalog as a trained adapter bank.


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
