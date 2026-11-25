# UMBRA Ω — Sovereign Worlds (v5.0.0)

**A playable, deterministic civilization laboratory and animated observatory.** This is a substantial **new prototype**, not a patch to the original live `chatgpt.site` instance or a modification of the unrelated EPOCH repository.

## Launch

Requires a modern web browser. No npm install, external models, API keys, cloud services, payments, login, or account access.

```bash
cd UMBRA_SOVEREIGN_WORLDS_v5
python -m http.server 8080
```

Open **http://localhost:8080** on the same machine. Serve over HTTP(S): ES-module imports generally don't work when double-clicking `index.html` as a `file://` document. To access on a phone over Wi-Fi, bind the server and use your computer's LAN address, with appropriate firewall/network controls. This does **not** create a publicly hosted service.

## v5.0 — The Living Accord

In addition to the v4 ecology simulation, this version adds **42 settlement councils, four faction systems, recurring synthetic elections, diplomatic corridors, mutual-aid transfers, ledger conservation checks, epidemic exposure, seven-axis sensitivity experiments and an on-demand Reality Court**. The research and UI components are implemented locally, but none of these mechanisms are empirically calibrated or remotely deployed.

**Tests:** `node --test tests/*.test.mjs` runs the deterministic model, civic ledger and Reality Court checks. `python tests/smoke.py` drives three browser viewports including civic controls and the court. Historical screenshots are not a substitute for rerunning the suites.

## Working features

| Feature | Implemented behavior | Evidence / limitation |
| --- | --- | --- |
| Civilization ecology | 42 geographic regions, ten initial colonies, resource and population dynamics, migrations, trade, founding, extinction | Explicit synthetic rule model in `engine.mjs` + `society.mjs` |
| Society and environment | Resource stock, healthcare, knowledge spillover, wealth, regional stress, conservation, emissions, climate and inherited traits | Not empirically calibrated; regional aggregates, not individual intelligent agents |
| Intervention engine | Seven tunable parameters with a deterministic seeded world reset | No inference about real policy outcomes |
| Temporal observatory | Play, pause, advance, variable playback speed, rewind, worldline comparisons | Rewind replay is deterministic; no server-side persistent history |
| Parallel-world experiment | 2–64 paired seeds; common exogenous random numbers; mean, dispersion and 5th/95th sample percentiles | Population differences are **model-internal**, not confidence bounds for real people |
| Observatory UI | Animated globe, routed trade lights, settlement selection/search, archive, mobile breakpoints, reduced motion | Canvas 2D, not 3D WebGL physically correct terrain |
| Computation | Versioned ES-module engine and separate experiment Web Worker (with a fallback) | Local in-browser simulation; no LLM, GPU model, or autonomous background agent |
| Records | Export/import seeded simulation passports, local SHA-256 checksum where secure context supports it | A checksum is **not** a digital signature; import recomputes model state |
| Diagnostics | Actual measured frame intervals, rendering and simulation step timings | No performance guarantees across devices |
| Safety | No connections to banks, brokerages, wallets, trading accounts or personal data | No claim to simulate real communities or deliver trustworthy forecasts |

**This build doesn't change your live UMBRA website.** The live site was inspected in read-only mode on 2026-11-22. It runs its own independent ecology and visual system. To publish this implementation, the host's original project/repository or deployment endpoint would need to be connected and a deployment separately authorized.

## Test

```bash
node --test tests/*.test.mjs
python -m pip install playwright
python -m playwright install chromium
python tests/smoke.py
```

The Node suite tests deterministic replay, equal-policy zero differences, model stability and corrupt-record handling. The Python Playwright suite tests desktop, tablet and mobile viewports. Tests use an inline test assembly to avoid restrictions on local server navigation; production serves the same exact source modules separately. **Neither test suite validates real-world model fidelity.**

## Source map

- `index.html`: semantic app markup.
- `world.css`: visual design, motion/accessibility and responsive layouts.
- `engine.mjs`: deterministic ecological model, scenario forks, sensitivity experiments and passport validation.
- `society.mjs`: civic councils, elections, diplomatic network, aid/fiscal transfers and balancing audits.
- `court.mjs`: independently replays worlds and reports engineering checks / scientific validation blocks.
- `observatory.mjs`: UI, animation, charting, controls and metrics.
- `lab.worker.mjs`: bounded off-thread experiment worker.
- `tests/`: reproducibility, civic conservation, negative testing, court and browser-smoke verification.
- `docs/MODEL_CARD.md`: protocol-style model card, methods and limitations.
- `docs/PROTOCOL.md`: experimental methodology and safeguards.
- `docs/ROADMAP.md`: long-horizon research/build program with proof gates.
- `docs/HANDOFF.md`: engineering continuation and host integration requirements.
- `docs/AUDIT.md`: original-site evidence and exact shipped status.
- `AGENTS.md`: coding and review rules.

## Governance

The project makes **no trading, profit, policy recommendation, real-world prediction, artificial-person consciousness, or autonomous-agent claim.** This is a fictional, programmable simulation and a basis for controlled research. Source code and rules must be audited before relying on generated results for consequential decisions. Research directions and possible integrations in `docs/ROADMAP.md` are *not shipped capabilities*.

## Research references

- Grimm et al., [ODD protocol for describing agent-based and other simulation models, second update](https://www.jasss.org/23/2/7.html) (2020). This documentation uses ODD-inspired reporting; **the current engine is an aggregate model, not a micro-agent ABM**.
- NetLogo, [BehaviorSpace experimental methodology](https://docs.netlogo.org/behaviorspace) and documented random-seed experiments. UMBRA implements its own seeded experiments, not NetLogo or BehaviorSpace.


### AUTOGENESIS Ω (bounded synthetic learning)
See [AUTOGENESIS documentation](docs/AUTOGENESIS.md). Adds 100 strategy-role configurations, paired-seed exploration, learned numerical reward prediction, disjoint holdout promotion, checkpoint integrity and bounded owner-local endpoints. No independent trained agent fleet, native-model training, deployment or scientific qualification is implied.


### Agentic Nexus Ω
See [Agentic Nexus](docs/AGENTIC_NEXUS.md) for the owner-local council, native BERT inference, experience bank, replay-verified training and adaptive model routing. Synthetic evaluation only; native pretrained inference and broad agentic capability remain unqualified.


### Hugging Face-backed weight cache
See [HF weight cache](docs/HF_WEIGHT_CACHE.md): owner-only eviction and checksum-pinned restoration of original public single-file native weights, remote registry and opt-in supported-model retrieval. No automatic deletion, private uploads or Ollama weight eviction.


### UMBRA INFINITY Ω
See [INFINITY](docs/INFINITY.md) for the autonomous public model discovery, bounded retrieval qualification, managed-cache rotation, local scheduling and current limitations.


### Intelligence gap detection and consolidated handoff
See [Gap detection](docs/GAP_DETECTION.md) and [Master handoff](docs/MASTER_HANDOFF_20261124.md) for evidence-driven capability assessment, benchmarked local models, deterministic fallbacks, discovery prioritization, automatic audit scheduling, and remaining qualification work. No broad intelligence or production qualification is asserted.


### MEGASWARM Ω and native training
See [MEGASWARM](docs/MEGASWARM.md) for the 4,096 shared-weight agent population, verified cross-model teaching, numerical learning and research, native training bootstrap, autonomous scheduling, pilot LoRA gates, evidence and unresolved limitations. Logical agents are not independent trained weight copies; native fine-tuning remains unverified pending download and RAM admission.


### Progressive swarm academy
See [SWARM_ACADEMY](docs/SWARM_ACADEMY.md) for ten-tier verified task generation, student-to-teacher lineage, the fixed 7B reference target, native adaptive LoRA growth, resource limits, and remaining qualification work.


### Market Academy Ω
See [MARKET_ACADEMY](docs/MARKET_ACADEMY.md) for 24 market lanes, ten tiers, source-reviewed mechanism questions, verified teaching/evaluation separation, native corpus expansion and empirical market-data roadmap. No trading authority or demonstrated market prediction ability.


### OMNISCIENCE knowledge and session recovery
See [OMNISCIENCE](docs/OMNISCIENCE.md) for the six-division curriculum and pinned, disabled external capability registry, and [session recovery ledger](docs/SESSION_RECOVERY_LEDGER_20261125.md) for the recoverable requests, verified work, constraints and outstanding tasks.


### Local repository fabric
See [LOCAL_REPOSITORY_FABRIC](docs/LOCAL_REPOSITORY_FABRIC.md) for the mounted-drive and WSL discovery, existing MYRIAD manifest reconciliation, shared source registry, verified agent inheritance and post-acquisition qualification gates. Local source availability is not executable integration.


### Verified repository execution and learning
See [REPOSITORY_EXECUTION_LEARNING](docs/REPOSITORY_EXECUTION_LEARNING.md) for five real pinned numerical adapters, source browsing, six replayed repository lessons, complete corpus audit, scheduler readiness gate, download recovery and remaining qualification work. This does not certify whole-package execution or trained LLM weights.


### Acquisition recovery
See [ACQUISITION_RECOVERY](docs/ACQUISITION_RECOVERY.md) for the resumed Q8 and neural/tiny queue, automated retries, reuse of installed CPU PyTorch, storage admission and actual outstanding downloads.
