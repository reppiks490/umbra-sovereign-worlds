# UMBRA Ω — canonical GitHub repository handoff

**Target repository name:** `umbra-sovereign-worlds`

**Target full name:** `reppiks490/umbra-sovereign-worlds`

**Remote state:** The owner created `reppiks490/umbra-sovereign-worlds`; this v5 package is intended for that repository. Do not assume any particular commit or deployment without reading GitHub itself.

**Reason to keep separate:** EPOCH Ω (`reppiks490/all-of-the-build-as-they-are-as-of-2-13am-9-26-2026`) is a distinct financial research prototype. UMBRA Ω is a distinct civilization/ecology simulation. The live UMBRA `chatgpt.site` deployment is also distinct and has not been modified.

## First agent actions after cloning the repository

1. Verify the repository is exactly `reppiks490/umbra-sovereign-worlds`, check the current HEAD and all open pull requests, then preserve unrelated work.
2. Verify the remote `README.md`, `AGENTS.md`, `engine.mjs`, `index.html`, `observatory.mjs`, `lab.worker.mjs`, `world.css`, `docs/`, and `tests/` files after upload. Check their file hashes if possible.
3. Run `node --test tests/*.test.mjs` and `python tests/smoke.py` with Playwright and Chromium installed; note the browser suite currently expects `/usr/bin/chromium`.
4. Start work by reading `AGENTS.md`, `docs/HANDOFF.md`, `docs/PROTOCOL.md`, `docs/MODEL_CARD.md`, `docs/AUDIT.md`, and `docs/ROADMAP.md`.

## Baseline / environment

- Standalone ESM app; no npm build required.
- Start with `python -m http.server 8080` in repo root and open `http://localhost:8080`.
- Unit tests: **31/31 passed locally including Reality Court tests** in the artifact workspace.
- Browser smoke: **3/3 passed** on 1440×900, 390×844 and 768×1024 with Chromium, using test's inline module fallback.
- No production network-hosted build test, Web Worker integration test or calibration benchmark has passed.
- The public `chatgpt.site` deployment is a distinct build; no update to that host was performed. GitHub verification status must be established from current remote state.

## Agent boundaries

- Engine: deterministic physical/ecological rule model, exports, seeded experiments, rigorously labeled synthetic.
- Observatory: frontend/animation/accessibility/real FPS measurements.
- Validation: Node tests (including society and court), browser smoke, provenance and negative tests.
- Research: calibration, external datasets/license, comparative experimental methods.

No agent may claim that individual AI citizens, accurate economics, actual population predictions, GPU worlds, or reliable policy interventions are implemented. Those are roadmap items gated on independent evidence.
