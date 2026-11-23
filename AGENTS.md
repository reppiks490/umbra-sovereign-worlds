# UMBRA Ω — Agent handoff and development rules

## Primary mission

Evolve a beautiful, instrumented, scientifically honest synthetic living-world laboratory without presenting the fiction as validated real ecology, policy, or intelligent persons. The `README.md`, `docs/MODEL_CARD.md`, `docs/PROTOCOL.md`, `docs/ROADMAP.md`, `docs/HANDOFF.md` and `docs/AUDIT.md` are the knowledge layer. Update them in the *same change* as substantive source changes.

## Architecture and ownership

- `engine.mjs` owns deterministic world/ecology rules, while `society.mjs` owns synthetic civic mechanisms and double-entry transfer accounting. Both are DOM-independent and Node-testable.
- `archive.mjs` (UM-101 feature branch) owns bounded SHA-256 checkpoint archives, independent genesis verification and import rejection. See `docs/ARCHIVE.md`. Do not claim persistent storage or digital signatures.
- `court.mjs` owns independent replay and engineering/scientific-status gates.
- `observatory.mjs` owns browser UI, rendering, event wiring and graphics telemetry; do not mix business rules into it.
- `lab.worker.mjs` owns off-thread experiment invocation; preserve deterministic equivalence with the fallback.
- `world.css` and `index.html` own responsive presentation and accessible semantics.
- `tests/` owns executable proof for claims.
- Preserve saved seed/replay semantics when modifying the engine; bump `ENGINE_VERSION` on incompatible behavior and update model cards.

## Change process

1. Inspect current files and status and honor all unrelated edits; do not auto-merge or force-push.
2. Record scope, high-risk claims, data rights, and knowledge-layer delta by exact path.
3. Implement bounded change; validate event-count, resource finite/nonnegative constraints and seed reproducibility.
4. Test `node --test tests/*.test.mjs` (including `tests/archive.test.mjs` for archive changes); for UI, test `python tests/smoke.py` on multiple viewport sizes, zero console/page errors and reduced motion.
5. Document assumptions, mechanics, evidence, limitation, and tested/unverified status.
6. Do not connect real finances, personal data, public policy datasets, LLM agents, external services, or deployment without a separate explicit permission + consent/data-rights design.
7. Keep current `chatgpt.site` domain unchanged until its source and deployment permissions are verified.

## Model integrity rules

- Synthetic result is labeled synthetic wherever displayed.
- Paired-seed effects are within-model and not empirical causal effects.
- Performance telemetry must measure actual displayed frame intervals rather than theoretical throughput.
- Exports never impersonate cryptographic signatures. Secure-context checksum is optional; import must verify a present checksum.
- No arbitrary code execution from imported JSON. No `eval`, nontrusted HTML injection, or unlicensed API fetching.
- Never hide unverified modules or claim absent tests were executed.
