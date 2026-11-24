# UMBRA Ω — FULL ENGINEERING TAKEOVER / BATON PASS

**Status: HANDED OFF TO NEXT CHAT.** Snapshot prepared 2026-11-22 America/Chicago (some GitHub timestamps are 2026-11-23 UTC). Re-fetch branch heads, Actions runs and review state before changes: this is not a live lock. This document supersedes the outdated v4-only main-branch handoff.

## First: exact identity and shipped/draft boundaries

**Canonical prototype repo:** https://github.com/reppiks490/umbra-sovereign-worlds . Main is v5.0.0, The Living Accord, exact verified baseline commit fb5d532785056331174d616820fe19856e331a03.

**Existing PUBLIC website, separate from the repo prototype:** https://umbra-focus-orbit.orange-cake-1541.chatgpt.site/ . The authoritative edit/deploy source for this ChatGPT Site has NOT been identified. No PR in this handoff has been merged or deployed there. Do not overwrite the live website, Decision Atlas, or Focus Timer.

**Visual handoff package from the prior chat:** UMBRA_Omega_Visual_Build_Package.zip; 9,244,660 bytes; SHA-256 97a9ce22c28a612c4f896af75a076320310ae33ec9190e295affbe729bc2f1f3. It includes source/ (v5 plus proposed PR #9-style heatmap renderer), preview/UMBRA_Omega_Full_Interactive_Visual_Preview.html (self-contained with inlined modules and Worker fallback), a real Chromium-captured animated GIF, desktop/iPhone screenshots, 31-test source suite and release-status notes. Ask the owner to **attach this ZIP** to the new chat: old sandbox paths are not necessarily accessible across chats. The standalone HTML SHA-256 was 89de37a63dbe32d04246aea936cceb32a9ea6c6f7e5d1fd3d981712b85771fd7. The GIF SHA-256 was dface6bc0cbdb2eec5d53df83d40ce83efb6d637cec16eb8b51f8c1a98c8e271.

**Never claim that visual ZIP includes the separately drafted #4, #7, #8 features in its interface.** The ZIP is not a combined, reviewed release; screenshots and GIF are visual evidence, not proof of production hosting.

## What MAIN v5 actually implements

- engine.mjs: 42 fixed synthetic geographic regions, ten starting settlements, rule-based births/deaths/migration/founding/extinction, 7 policy sliders, resources, disease, carbon, biodiversity, keyed seeded randomness, paired-seed exploratory experiments.
- society.mjs: settlement councils, four factions, recurring synthetic elections, diplomatic corridors, double-entry civic transfer accounting, aid/epidemic coupling and ledger audit.
- court.mjs: engineering Reality Court; 8 engineering checks, 5 real-world scientific or release claims BLOCKED by design.
- observatory.mjs + index.html + world.css: interactive animated Canvas 2D globe, orbit drag/zoom, site list/selection, play-pause-step-speed/rewind, metrics, alternate worldlines, Reality Forge, civic atlas, experiments, local export/import, adaptive rendering and *measured* frame/step timing.
- lab.worker.mjs: in-browser experiment Worker with fallback; no hosted agent infrastructure.
- tests/: 31 baseline Node tests and Chromium viewport smoke on the original main branch. The original inline smoke forcibly disables the real Worker. AGENTS.md and docs/MODEL_CARD.md, docs/PROTOCOL.md, docs/ROADMAP.md, docs/AUDIT.md and docs/VERIFICATION.md provide rules and methodology.

The simulation is **rule-based, synthetic, uncalibrated, settlement-aggregate**—NOT human-level citizens, real causal effects, environmental forecasting, an actual GPU terrain engine, a durable multiplayer server or a financial trading service.

## Four independent DRAFT / UNMERGED feature branches

**#7 Real ESM / Worker browser verification:** https://github.com/reppiks490/umbra-sovereign-worlds/pull/7
Branch: test/um-103-served-worker-browser
HEAD: bc6ebf78a919aa331b4c7dcff2337f58b409992e
New tests/served_smoke.py starts actual HTTP server, tests module graph/real Worker, malformed protocol rejection, forced mobile fallback; GitHub Actions [run 45099180990](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45099180990) passed 31 Node, original three browser viewports and new served tests. Independent review and integrated CI still pending.

**#4 Content-addressed world archive:** https://github.com/reppiks490/umbra-sovereign-worlds/pull/4
Branch: feature/um-101-content-addressed-archives
HEAD: e1be6a6ce530d0b81b28194593efb3cd014b3e1d
New archive.mjs + tests/archive.test.mjs + docs/ARCHIVE.md. Immutable, local-only SHA-256 chained synthetic checkpoints, independent replay from genesis, 20-seed and 520-turn tests, byte/tick/count limits. GitHub Actions [run 45102214497](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45102214497) passed **47/47 Node** and 3 browser viewports. **BLOCKING SOURCE-REVIEW SECURITY ISSUE BELOW: green CI does not establish safety**. Not actual persistent server storage, cryptographic authentication or empirical validation.

**#8 Preregistered synthetic research tournament:** https://github.com/reppiks490/umbra-sovereign-worlds/pull/8
Branch: feature/um-103-preregistered-research-tournament
HEAD: 7697a3c2646773652047417f5bd591846eeea76c
New research.mjs + tests/research.test.mjs + docs/RESEARCH.md. Fixed 20-64 synthetic seeds, 75/25 synthetic exploration/confirmation partition, per-seed same-policy null control, structural and civic checks, per-seed outputs. [Run 45102227631](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45102227631) passed **40/40 Node** plus 3 browser sizes. Still needs independent review and 64x240 performance profiling. Synthetic seed partitions do NOT constitute empirical validation.

**#9 Interactive planetary data lenses:** https://github.com/reppiks490/umbra-sovereign-worlds/pull/9
Branch: feature/um-102-planetary-data-lenses
HEAD: 3933229912a8c8c447a635a2ad1cba95464e00a8
New Canvas projected fields and selector: population, food/water scarcity, disease burden, climate exposure, low council support and OFF. Derived from existing model, adaptive rendering, reduced-motion support, browser diagnostic state. [Run 45103450678](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45103450678) passed **31/31 Node**, 3 viewport browser checks (1440x900, 768x1024, 390x844) and additional reduced-motion phone check; zero reported JS errors and horizontal overflow. Not WebGL or verified iPhone p50/p95, not deployed.

**CRITICAL BRANCH COLLISION:** These four drafts were independently branched from main. They all touch shared README/AGENTS/HANDOFF/ROADMAP/VERIFICATION documentation, so independent green PRs do NOT prove an integrated release. Need explicit conflict reconciliation and combined CI; no blind squash, auto merge or overwrite.

## NEW P0 SECURITY FINDING from hourly autonomous review (not yet fixed)

The confirmed active UMBRA Verified Evolution hourly ChatGPT automation inspected #4 and submitted GitHub **review ID 6016405926** on 2026-11-23 UTC. It found a plausible accessor-execution flaw in archive.mjs: header() calls byteLength(JSON.stringify(archive)) **before** canonicalize() rejects getter-backed or non-JSON properties. If programmatic callers pass objects with enumerable getters or own toJSON hooks, JSON.stringify can invoke them, violating the claim of never executing caller accessors. importArchive(json) is narrower because JSON.parse yields plain data; object-accepting verifyArchive(), appendCheckpoint(), exportArchive() remain exposed.

**Finding evidence = STATIC SOURCE REVIEW ONLY, not a tested exploit. No fix, new tests or post-fix CI has been verified.** Before any archive merge: re-read review+current code; implement bounded safe descriptor traversal or safe canonical byte-size enforcement BEFORE JSON.stringify; regression-test getter counter and toJSON trap (must remain zero), malformed/sparse and oversized objects, while preserving replay correctness; check maximum-size performance; obtain independent review and fresh CI.

## Live website route / user-data preservation (P0 Issue #5)

**Route /**: Living World. Public files include broadcast.mjs -> ecology.mjs, planet.mjs, motion.mjs; ecology.mjs -> sites-world.mjs; planet.mjs uses lithosphere.webp. Motion bundle observed ~391 KB, containing Remotion-related code, requiring actual license/source review before porting. Its internal world rules differ from GitHub v5.

**Route /decisions.html and /decisions**: Decision Atlas, atlas.js and atlas.css. Browser localStorage key **umbra-atlas-v1** stores task data. Sends task/length through a focus.html URL hash.

**Route /focus.html**: Focus Timer, app.js and CSS. Browser localStorage key **umbra** stores timer/session data.

The original ChatGPT Site editor/deployer has **not** been identified. A GitHub push does NOT deploy this domain. Do not read or wipe actual tasks/timer state. Before replacement: identify authoritative source and deployment permissions, capture exact assets and route baseline, test all three routes with synthetic localStorage fixtures, verify asset rights, build preview/rollback and get explicit owner approval. See https://github.com/reppiks490/umbra-sovereign-worlds/issues/5.

## Work tracking / next release path

- #1 archive and temporal authority https://github.com/reppiks490/umbra-sovereign-worlds/issues/1
- #2 cinema/visual GPU mobile experience https://github.com/reppiks490/umbra-sovereign-worlds/issues/2
- #3 scientific and engineering validity https://github.com/reppiks490/umbra-sovereign-worlds/issues/3
- #5 live deployment provenance and 3-route protection https://github.com/reppiks490/umbra-sovereign-worlds/issues/5
- #6 licensed evidence gateway / maturity matrix https://github.com/reppiks490/umbra-sovereign-worlds/issues/6
- **#10 integration** https://github.com/reppiks490/umbra-sovereign-worlds/issues/10 — no integrated branch or merged release yet.

**Next agent priority (do NOT re-ask the owner for already documented info):**
1. Fetch current main SHA, four PR heads, their CI and security review; check whether the hourly automation or another writer has already fixed archive #4.
2. Repair and independently verify #4's getter/toJSON defect on its own branch or draft PR. Do not describe green CI from before this discovery as fix evidence.
3. Coordinate #10 integration branch. Suggested review/test order: #7 served real Worker, #4 vetted archive, #8 research, #9 visuals. Reconcile common docs and run **observed** combined Node, real HTTP-served ESM/Worker, browser sizes, reduced-motion, import/export, visual performance tests. Do not infer combined test count by addition.
4. Pursue truly animated, dense, model-state-driven visual world with measured p50/p95 display-frame costs on an actual iPhone and desktop; preserve mobile accessibility, reduced motion, prior v5 UI controls. No false "5000 FPS" or fake fully autonomous citizens.
5. Locate actual live ChatGPT Site editor and deploy chain; preserve three live routes, storage contracts, and license/rollback. A production deploy is a separate decision.
6. Continue eight constellation roadmap (docs/ROADMAP.md) only with explicit implemented/tested status, not speculative claims.

## Reproducing tests / preview

- Node 22+: node --test tests/*.test.mjs
- Playwright Chromium: python -m pip install playwright; python -m playwright install chromium; python tests/smoke.py
- On draft #7: additionally python tests/served_smoke.py (actual HTTP server, real module Worker).
- To see the source in the visual ZIP: extract, cd source, python -m http.server 8080; browse http://localhost:8080.
- The standalone preview/UMBRA_Omega_Full_Interactive_Visual_Preview.html is self-contained with inlined JS and worker fallback. A capable browser is required. Prior captured screenshots/GIF are actual Chromium render output, NOT an online site deployment.
- The visual package was checked to contain 33 ZIP entries, including source, preview HTML, GIF and desktop/iPhone PNGs. Its underlying Node suite was 31/31. In-browser pause/step/experiments/Court were exercised with court 8 pass, 0 fail, 5 blocked. New executions should independently rerun on current SHA.
- There is no checked-out Git worktree in this handoff; edits and PR creation were through the connected GitHub plugin. No dirty working tree is asserted.

## Automation / account boundaries / user's non-negotiables

UMBRA Verified Evolution task ID: Automation_e9175db64aa08191a302c3358790867a. Confirmed **enabled**, scheduled hourly, America/Chicago. Its last reviewed result detected the #4 security finding. Runs are bounded—not continuously live agents—and may alter draft branches or submit reviews between chats. Re-fetch remote state before writing.

User wants massively ambitious, cinematic, fully **moving** visuals and a working iPhone link. Past user feedback rejects static carousels, fake assurances and inaccessible links. Prioritize actual browser rendering, end-to-end animations and verified deployments over elaborate plans.

**Do not use OpenAI Codex in any UMBRA scheduled/looped automation.** No unauthorized real trading, personal Finances/banking/wallet access, secrets, paid provider use, user-data migration, unrelated ICARUS/EPOCH edits, destructive history/force pushes, PR auto-merges or live website cutovers. Plugin mentions do NOT mean every named app is installed or its capabilities were run. Independent synthetic worlds are not validated real communities.

## Knowledge delta / baton ownership

**Before**: main's handoff still claimed v4, 12 tests and missing served-Worker evidence. **This docs-only branch** records actual main v5, all four PRs with head SHAs, CI, security review, visual artifacts/hashes, three live routes, distinct browser storage keys, active automation and precise next actions.

Owner transition: Previous chat **stops** at the completed handoff; next chat should run a Baton Pass foresight audit against GitHub before editing. This docs branch changes only documentation; it neither merges code nor updates the public website. Stale if any PR HEAD, CI, site host provenance, artifact package, active automation or GitHub issue changes.

**Verification verdict: HANDOFF READY; PRODUCT INTEGRATION NOT DONE; PRODUCTION DEPLOYMENT UNVERIFIED; ARCHIVE SECURITY REMEDIATION OPEN.**
