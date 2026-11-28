# UMBRA INFINITY Ω
Autonomous public model discovery, qualification and managed-cache rotation. This is an implemented bounded retrieval lane, not general autonomous intelligence. The scheduler is a local Windows interactive-user task every 30 minutes. It uses no Codex, paid inference, private uploads, or external code. The first acquisition queue and Q8 must be complete before any new weights are fetched or evaluated. Metadata-only discovery is permitted during that queue and refreshed at most once daily.

Discovery queries six public Hugging Face task categories, up to 30 results each, and marks the results unverified. Candidate execution is restricted to the two currently implemented native BERT-family adapters. Revisions, permissive license, public access, sizes, and SHA-256 are checked before acquisition. The worker prefers an exact model in the initial local pool; otherwise uses a separate INFINITY cache with a 1 GB nominal cap and 8 GB free-space floor (5 GB Windows, 3 GB learning). Only its own verified original weights may be automatically evicted after qualification or rejection, excluding the champion. Initial acquisition assets, Ollama models, personal files, learned weights and checkpoints are never automatically removed. The model source may become unavailable.

Qualification measures six synthetic semantic retrieval cases using actual local embeddings and a minimum 5/6 accuracy plus positive mean similarity margin. The benchmark is small and not independent general capability evidence; a champion is qualified only for this test. Profiles are revision-specific. One candidate per cycle; failed candidates retry after 24 hours. Inference selects the current champion and can restore its exact registered original weights. Other families remain discovery-only. This does not train external model weights or implement general-purpose autonomous reasoning.

Owner operations: infinity_status, infinity_embed with synthetic mission seed/steps. Requires the existing reviewed native Python/root environment. State and discovery live outside Git under the private acquisition root/infinity; service-status.json records scheduler status. The scheduled task UMBRA-Infinity-Local-20261124 runs scripts/infinity_service.cmd under the interactive owner account, every 30 minutes; it will not run while the PC is off or logged out and Windows battery policy may block it. No existing automations modified. If queue fails or an acquisition lock is stranded, the worker defers rather than removing a possibly live lock. The code is not merged to main. Test commands: npm test; Python unittest discovery test_infinity.py, test_hf_weight_cache.py, test_agentic_native.py. Full Node 121/121; Python 13/13 passed. Live qualification requires real weights after the initial acquisition queue.

Deployment evidence (2026-11-24 local): Windows scheduled task UMBRA-Infinity-Local-20261124 created and enabled with 30-minute recurrence, interactive user only. First execution exited 0 and wrote service-status.json with status deferred_acquisition and 180 discovered public model candidates. The Q8 pull was still running (4.6 GB / 29 GB); no existing weights were removed. Discovery does not establish compatibility or performance.


### Intelligence gap detection and consolidated handoff
See [Gap detection](GAP_DETECTION.md) and [Master handoff](MASTER_HANDOFF_20261124.md) for evidence-driven capability assessment, benchmarked local models, deterministic fallbacks, discovery prioritization, automatic audit scheduling, and remaining qualification work. No broad intelligence or production qualification is asserted.


### MEGASWARM Ω and native training
See [MEGASWARM](MEGASWARM.md) for the 4,096 shared-weight agent population, verified cross-model teaching, numerical learning and research, native training bootstrap, autonomous scheduling, pilot LoRA gates, evidence and unresolved limitations. Logical agents are not independent trained weight copies; native fine-tuning remains unverified pending download and RAM admission.


### Acquisition recovery
See [ACQUISITION_RECOVERY](ACQUISITION_RECOVERY.md) for the resumed Q8 and neural/tiny queue, automated retries, reuse of installed CPU PyTorch, storage admission and actual outstanding downloads.
