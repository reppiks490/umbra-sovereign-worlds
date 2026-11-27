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

## UM-110 settlement integrity (2026-11-23, proposed)
- New Node adversarial cases cover deleted sparse slots, undefined/null entries, missing population, NaN food and infinite water; each requires G01/G02/G03 failure as appropriate and G07 blocked when replay cannot safely inspect malformed state.
- Existing valid-world Court checks must still pass; run `node --test tests/*.test.mjs` and `python tests/smoke.py` at exact PR head.
- No CI success is claimed until the GitHub Actions run and SHA are observed. This does not validate empirical ecology or the separate live public site.

## UM-110 native replay-budget regression (2026-11-26)
- Parent: 86368f0876740c6d3ed94e8b0df4500bcc50d7a1; source engine 62b23d9dfa06be5761be20eb5c14c45c8c86f022, society 9ae65c5917e4c0084bda7e681ff0624e419ec42f, Court before f2cab51609b9f204d4301a821a125e94e43960c7. All original Node test and package blobs matched GitHub.
- Native Node v22.16.0 in isolated scratch environment, no dependency installation: node --test tests/court-replay-limit.test.mjs RED 2 passed / 11 failed; same command after correction GREEN 13 passed / 0 failed. npm test GREEN 46 passed / 0 failed / 0 skipped. Candidate Court 91d83c0133909f606663f96aca74d3b76dcb6b8e, new test 9f10ba48edd468e8820bcd84a77b75a0f92ecc7c.
- Regression covers real 5001-turn chunked advancement, default/raised/reduced/zero budget, malformed tick values, invalid caller budget and valid boundary replay. Existing finite-negative corruption test now passes. G07 compares selected rounded state rather than claiming a full canonical snapshot.
- Workflow preflight: complete branch workflow tree 4f0b710f909bf51e212991a9f7f68fe475a6fabf; 5300/5300 generated manual-only workflows matched reconstructed reviewed templates by Git blob SHA-1. Four other workflow definitions reviewed; main workflow inventory compared, main-only scheduled research lanes not triggered by this branch. Existing PR-triggered synthetic and browser qualification is separate. No changes to CI schedules or workflows. Full exact-head CI, combined integration, live website and real-device browser tests unqualified here. The legacy 300-workflow validator also appears to count the advanced workflows; owned by UM-107, do not conflate with this fix.


### 2026-11-27 ? UM-110 topology audit correction

G01 now rejects sparse/malformed regional coordinates and six-neighbor maps, while G07 blocks malformed topology and compares the fixed seeded topology even when all records have valid shapes. RED: both new adversarial tests failed (false PASS). GREEN: 2/2 focused, 48/48 full Node suite, zero failures/skips. No simulation rule changes, deployment, or independent browser qualification.
