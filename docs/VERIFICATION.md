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

## UM-106 replay-bound integration — 2026-11-26

Parent c9c682db768dd35fca411dd5bdadcdad23cbb8df; UM-110 source bc1cf1ad727fc5de95851cb434fb5125307aa4da; native Windows Node v26.13.0. Exact 39 source/test/data blobs verified before execution. Full Node suite with --test-concurrency=1 --test-reporter=tap: RED 63/74 (11 replay regressions, exit 1, 4.359 s), GREEN 74/74 (0 skipped, exit 0, 4.609 s). RED log SHA256 38edb3ef01e24b174713607775a47b0549c052c653d099a2a706ea1023f19fae; GREEN 554529c30134d5cd73579ff82de852886b562210ddfbb2777f26b33ad8ebc130. Candidate Court Git blob 3ccd3a58e494ff622f38a8e76861c362b14a6baa; imported test blob 9f10ba48edd468e8820bcd84a77b75a0f92ecc7c. Initial Node 26 default reporter produced readable failures but failed TAP parsing; rerun explicitly selected TAP. No source-engine, civic, browser or workflow changes. These are native software tests, not browser, scientific or model qualification.
