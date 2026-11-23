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

## UM-107 CI execution bounds (proposal, 2026-11-23)

The draft CI-only branch sets unit timeout-minutes=12 and browser timeout-minutes=25, retains contents:read, and sets cancel-in-progress:false on the verification concurrency group. tests/ci-contract.test.mjs asserts these controls, the unchanged npm test and Playwright smoke commands, and the 1440/390/768 viewport list. This is a source-level policy regression, not an end-to-end security proof: it cannot establish GitHub-hosted runner integrity, dependency pinning, true reproducibility, or public-site compatibility. Record the exact commit and run URL after CI executes; no passing result is assumed by this documentation.
