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

## UM-110 Court settlement integrity (draft branch, 2026-11-23)
- Branch `fix/um-110-court-dense-settlements` addresses issue #20 independently of PR #16's civic auditor.
- G01 rejects sparse/null/undefined settlement entries; G02 requires own finite nonnegative resource fields; G03 cannot pass on invalid settlements. G07 blocks unsafe replay rather than treating missing records as validated.
- No simulation rules, UI, browser storage, or live website changed. Node and browser GitHub Actions at the final PR head remain the release gate; do not infer a pass from source review.

## UM-110 replay bounds follow-up (2026-11-26)
- Parent 86368f0876740c6d3ed94e8b0df4500bcc50d7a1. Addresses the reproduced G07 exception and malformed-turn false G01 pass from PR #25 review 6077983774. No engine or society behavior changed. A valid long-running world remains valid; a single replay never exceeds the existing 5000-turn engine limit. Invalid caller budgets block replay with an explicit reason. Finite corrupted settlement resources remain replayable for mismatch detection, not treated as valid.
- New native regression file: tests/court-replay-limit.test.mjs. Exact parent source and original test blobs verified against GitHub; Node v22.16.0: RED 2/13, GREEN 13/13; complete npm test suite 46/46, zero skipped. See docs/VERIFICATION.md. This is not browser or empirical qualification.
- Candidate Court blob 91d83c0133909f606663f96aca74d3b76dcb6b8e; regression blob 9f10ba48edd468e8820bcd84a77b75a0f92ecc7c. CI/browser acceptance pending at published head. Preserve PR #25's existing civic guards during integration, do not overwrite its Court file wholesale. Next: reconcile the bounded replay changes into UM-106 and run native combined and served-browser qualification. Existing sparse topology, civic endpoint range, archive and migration semantics are separate ownership. No merge/deploy.
