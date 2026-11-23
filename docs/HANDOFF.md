# Engineering continuation handoff

## Present deliverable

New standalone web prototype **UMBRA Ω Sovereign Worlds v5**. Entry: `index.html`, source: `engine.mjs`, `observatory.mjs`, `lab.worker.mjs`, `world.css`. The experiments are deterministic synthetic *regional* models. No local/remote backend and no persistent autonomous agents. Tests and run instructions in README.

## Separately identified projects

- Original live `https://umbra-focus-orbit.orange-cake-1541.chatgpt.site/` is an *existing, separate* civilization experience. We inspected its published sources but could not identify/edit its origin/deployment.
- `reppiks490/all-of-the-build-as-they-are-as-of-2-13am-9-26-2026` has **EPOCH Ω v3** source. Preserve it. Don't copy UMBRA over EPOCH without user authorization.

## Next iteration priorities

**First:** the separate UMBRA source repository is now `reppiks490/umbra-sovereign-worlds`. The original live site's source/deployment pipeline is still unverified; do not assume GitHub changes deploy there. Preserve the baseline and verify CI/diff before merging. No force pushes.

**Second:** separate engine simulation and renderer with a proper hosted ESM build/instrumentation; use browser hardware tests, control CPU/GPU budget, avoid misleading FPS targets.

**Third:** pursue research gates in `docs/ROADMAP.md`, starting with true append-only world persistence, bitemporal event provenance, empirical calibration if intended for scientific claims, and agent-based person-level models only with explicit design and independent verification.

**Fourth:** add content accessibility and keyboard navigability, testing with mobile Safari / WebKit, a worker runtime test on a real HTTP host, and benchmark registration. Archive experimental seeds before changing rules.

## Tested acceptance

The v5 baseline had 31/31 local Node tests passing before the UM-101 branch. New archive tests are not yet verified. Three browser-size smoke checks pass under inline test harness. Source import with secure browser context and production network hosting remain untested. No live site changes/deploys. Model fidelity not validated.

## Stop / release criteria

Never claim a branch/PR/merge/hosting release exists without checking provider responses. All published claims must map to code and test evidence; mobile appearance is not a performance guarantee. Keep financial integrations opt-in and sandbox-only until a separate mandate and compliance controls. See `AGENTS.md` for guardrails.

## UM-101 continuation (feature branch, not merged)

The proposed `archive.mjs` and `tests/archive.test.mjs` introduce portable chained snapshots, independently verified genesis replay, bounded input and explicit no-signature/no-server limits. Read `docs/ARCHIVE.md`; run `npm test`; inspect GitHub Actions results and review before merging. Existing observatory UI is unchanged. Stale when this feature is merged or archive contracts change.
