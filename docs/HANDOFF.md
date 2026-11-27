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

## UM-106 replay-bound integration — 2026-11-26

Reconcile UM-110 bounded replay into existing UM-106 draft without replacing its civic safeguards. Parent c9c682db768dd35fca411dd5bdadcdad23cbb8df; UM-110 source bc1cf1ad727fc5de95851cb434fb5125307aa4da; native Windows Node v26.13.0. Exact 39 source/test/data blobs verified before execution. Full Node suite with --test-concurrency=1 --test-reporter=tap: RED 63/74 (11 replay regressions, exit 1, 4.359 s), GREEN 74/74 (0 skipped, exit 0, 4.609 s). RED log SHA256 38edb3ef01e24b174713607775a47b0549c052c653d099a2a706ea1023f19fae; GREEN 554529c30134d5cd73579ff82de852886b562210ddfbb2777f26b33ad8ebc130. Candidate Court Git blob 3ccd3a58e494ff622f38a8e76861c362b14a6baa; imported test blob 9f10ba48edd468e8820bcd84a77b75a0f92ecc7c. Initial Node 26 default reporter produced readable failures but failed TAP parsing; rerun explicitly selected TAP. No source-engine, civic, browser or workflow changes. These are native software tests, not browser, scientific or model qualification. Next: qualify exact-head CI and served browser, then coordinate #7/#4/#8/#9. No deployment.

## UM-106 corridor and PR verification - 2026-11-27

Parent 279392ba62a7654c763d5c477dbf7b79709fae01; isolated Windows checkout via LocalCommander. Corridor RED 0/1, GREEN Court 12/12; CI contract RED 0/1, GREEN 6/6; full Node TAP 111/111, zero skipped, 15.609 s. PR-only reusable call added to existing advanced workflow, unit workflow accepts workflow_call. Existing schedules and read-only permissions retained. Hosted fallback unverified. No live changes.
