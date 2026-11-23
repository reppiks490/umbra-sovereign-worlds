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

## UM-107 draft: bounded GitHub Actions verification (2026-11-23)

A separate, independent CI-only lane proposes finite verification job budgets (12-minute Node, 25-minute Playwright), read-only workflow permissions, and a non-cancelling concurrency group so new pushes do not erase the preceding run's evidence. A dependency-free Node regression test checks those workflow contracts and the existing 1440/390/768 viewport smoke command. This does not modify model state, UI, deployed sites, or browser localStorage. It does not pin third-party Actions or Playwright package versions and does not establish reproducible dependency provenance. Verify the exact PR head's GitHub Actions Node and browser results before treating this as accepted. Do not merge automatically. The existing separate public Living World, Decision Atlas, and Focus Timer remain outside this repository's deployment authority.
