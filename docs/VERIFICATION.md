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

## UM-102 planetary data-lens branch — verified CI, production not validated

`feature/um-102-planetary-data-lenses` extends `tests/smoke.py` to select all five synthetic data fields plus OFF on desktop/tablet/phone, checks the read-only diagnostic lens state, and tests a separate reduced-motion phone viewport. GitHub Actions [run 45103208648](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45103208648) on SHA `71ddd6c316e2433ba52852d50acd512924575378` completed successfully: **31/31 Node baseline tests**, **3/3 browser viewport smoke tests** (1440×900, 390×844, 768×1024), and **a separate reduced-motion 390px viewport test** (lenses interactive, zero JS errors and overflow). The browser suite inlines ESM and deliberately uses worker fallback. This does **not** establish served ESM in this branch, production deployment, independent usability review, or real-device iPhone GPU frame-time profiling. Stale when a subsequent commit or new renderer supersedes the recorded CI evidence.
