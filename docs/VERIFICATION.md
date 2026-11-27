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

## UM-103 preregistered research experiment — current observed CI

Branch `feature/um-103-preregistered-research-tournament` adds `research.mjs` and `tests/research.test.mjs`. Planned tests cover 20–64 seeded synthetic experiments, null controls, frozen manifest rejection and deliberately corrupted world snapshots. GitHub Actions [run 45101977810](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45101977810) on commit `344e31dced064525d286c970f18b5e08e3127958` completed successfully: **40/40 Node tests** (including 9 research tests), **3/3 browser viewport smoke tests** at 1440×900, 390×844, and 768×1024 with zero overflow. These tests do not establish external model validity or production deployment. Stale when a newer commit supersedes this run.
