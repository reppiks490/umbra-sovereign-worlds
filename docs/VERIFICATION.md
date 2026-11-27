# UMBRA v5 — Verified testing record

## Observed local results, 2026-11-22 (America/Chicago)

- `node --test tests/*.test.mjs`: **31/31 passed, zero failures**. Includes seven Reality Court adversarial tests, seeded deterministic trajectories, conservation of civic transfer ledgers, scenario comparison invariants and bounded sensitivity experiments.
- `python tests/smoke.py`: **3/3 viewport tests passed**, widths 1440px, 390px, 768px. Each test exercises pause/step, rewind, settlement search, intervention, paired experiment, Reality Court and civic-network layer switching. Reported 0 JS errors and 0 horizontal overflow.
- Browser tests used inlined module code and a forced worker fallback because the sandbox blocks direct local network navigation; production ESM HTTP and worker availability are **not** asserted to have been tested.
- A public workflow is included under `.github/workflows/unit.yml`; it must run in GitHub Actions before the CI state can be called green.

## Explicit nonclaims

No paper trading, brokerage or cloud account integration. No empirical model calibration. No real-world predictive validity. No independent per-person LLM citizens. No automatic deployment to the owner's existing `chatgpt.site` website. No cryptographic signatures or external audit attestation.

## Reproduction

```bash
node --test tests/*.test.mjs
python -m pip install playwright
python -m playwright install chromium
python tests/smoke.py
```

## UM-103 served-module verification proposal (separate feature branch)

A new `tests/served_smoke.py` uses a real localhost HTTP server, Playwright Chromium, actual ES-module imports, a real module Web Worker, negative protocol rejection and forced no-Worker fallback. It is added to the GitHub Actions browser job in the UM-103 branch. **Observed GitHub Actions:** [run 45099044163](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45099044163) on commit `d04d7eefd001651b0b63689d198b836b8bb91364` passed the existing 31/31 Node tests, three inline browser viewports and **three new real-served checks**: successful ES-module Worker experiment, invalid worker protocol rejection, and forced fallback on a phone. Browser job logs confirmed all three PASS lines. No independent review, production deployment or external model calibration is implied. This note becomes stale when a new workflow run supersedes this evidence.
