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

## UM-109 proposed verification (2026-11-23)

Source change: fail-closed `civicAudit` on NaN/infinite fiscal and food residuals and missing/null/non-array councils, corridors, ledger. Tests: new Node cases in `tests/society.test.mjs` asserting audit failures and Court G04/G05 failures. Execute `node --test tests/*.test.mjs` and browser smoke through GitHub Actions at the exact PR head; results must be recorded after observation, not inferred from source review. No empirical scientific validation or live-site deployment implied.
