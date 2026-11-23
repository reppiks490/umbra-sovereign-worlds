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

## UM-101 feature branch — unverified until CI

The proposed `archive.mjs` and `tests/archive.test.mjs` add adversarial SHA-256 chain, forged-hash, duplicate-tick, version, replay and input-limit checks. They were **not** executed locally in this ChatGPT environment. GitHub Actions [run 45098480527](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45098480527) on PR #4 commit `c5a10322e5fdef038e5fdec0e2a163b9a139b6b6` completed successfully: **44/44 Node tests**, zero failures, and **3/3 browser viewport checks** (1440×900, 390×844, 768×1024; zero overflow). The 13 additional Node tests are archive-focused. The browser tests still use the existing inline-module/fallback harness, not a real served worker. No independent security review, maximum-size performance benchmark, hosted integration or live deployment has been verified. Stale when this branch changes or a new workflow run supersedes this evidence.

## UM-101 follow-up audit — latest observed CI

At the owner's continuing request on 2026-11-22, serializer guards and twenty-seed/three-policy replay tests were added to PR #4. GitHub Actions [run 45101595936](https://github.com/reppiks490/umbra-sovereign-worlds/actions/runs/45101595936) on commit `287441dde00119d6fe2c5e3979a34e3331f7f1c1` completed successfully: **47/47 Node tests** (including 16 archive tests) and **3/3 browser viewport smoke tests** at 1440×900, 390×844 and 768×1024, with zero horizontal overflow. The entire Node suite finished in 3.85 s of test runtime. This does not constitute worst-case archive-size profiling or independent security review. Stale when a new commit supersedes this evidence. No external truth, hosted persistence or production integration is implied.
