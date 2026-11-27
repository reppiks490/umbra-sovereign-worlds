# Evidence and implementation audit

## Origin inspection — November 22, 2026

User-provided URL: https://umbra-focus-orbit.orange-cake-1541.chatgpt.site/

Site inspected read-only with Firecrawl and Parallel extractors, plus inspection of publicly served JavaScript modules using a remote read-only browser. Public page title: **Umbra · The Living World**. Observable UI: animated orbital world view, selected settlement telemetry, story dispatch, trade vs no-trade paired world counts, world chronicle. Live code referenced `broadcast.mjs`, `ecology.mjs`, `planet.mjs` and `motion.mjs`.

The live `broadcast.mjs` constructs `newWorld(era)` and a no-trade twin, advances each to `atTime(Date.now())`, and renders an HTML/canvas interface. The live `ecology.mjs` implements deterministic regional populations, food, founding, migrations, and trade shocks. It does not establish a remote persistent agent service. The live page's “On air” means the page is advancing, not proof of server-side agents.

**Site operation not changed.** The origin repository was not identified through the connected GitHub repository search. The previously connected `EPOCH Ω` repository is an unrelated project and was not overwritten. The `chatgpt.site` publishing endpoint is not available for authorized edits through our current connected tools.

## v4 output provenance

Created independently as a new static ES-module app in `UMBRA_SOVEREIGN_WORLDS_v4/`. The original UI's broad visual themes and synthetic civilization concepts are contextual references. v4 code is standalone, dependency-free code with newly defined rules and structures. v4 is **not a verified 1:1 upgrade of the original site's engine**, and its metrics should not be numerically compared against original live metrics as though they are the same model.

## Verification record

Executed locally:

- `node --test tests/engine.test.mjs`: **12 tests passed, 0 failed**.
- `python tests/smoke.py`: **3 viewport smoke checks passed** (1440×900, 390×844, 768×1024), zero Playwright page exceptions, zero horizontal overflow. Tests exercise step, controls, regional selection and a deterministic paired experiment.
- Visual full-page browser screenshots inspected manually for layout and readability; screenshot artifacts are available separately, not necessary for running the app.

Limitations of verification: scripts are served inline in the browser smoke test due local sandbox navigation restrictions. Actual deployment to a public host, hosted module resolution, iOS Safari device tests, worker behavior on an external host, real accessibility audit and performance benchmarks on user hardware **have not** been verified. Do not claim otherwise.

## Permission / account boundaries

No financial account, broker, wallet or private files used. No source keys accessed. No trades, API writes, paid model tasks, or changes to the user-provided `chatgpt.site` project. No GitHub source writes performed for UMBRA in this release. MagicPath external-agent quota was exhausted and not bypassed. No claims of multiple independent coding agents executing when they did not.

## UM-106 replay-bound integration — 2026-11-26

New isolated native software qualification at UM-106 parent: 74/74 after bounded replay correction. Original live three-route site and browser storage unchanged. Real-device/browser performance and public deployment remain unqualified.

## UM-106 corridor and PR verification - 2026-11-27

Local Node v26.13.0 full suite 111/111 (no failures/skips); both new tests failed before repair. Native log SHA256: 1D06858E98139CBFCF7E197F26B1ADB6E83DEDE1A16D173553346C67D490210C. Browser and hosted jobs on candidate head not yet verified; no independent scientific validation, deployment, data-rights expansion or trading changes.
