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
