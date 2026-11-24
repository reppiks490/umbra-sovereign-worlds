# MYRIAD Ω × UMBRA — v2.0: independent algorithms, recoverability, and worker fencing

**Status:** Research implementation on review-only `reppiks490/umbra-sovereign-worlds` PR #21. No automatic merge, production deployment, trading, or autonomous model-weight promotion. Prior MYRIAD 13/13 release gates still apply.

## Implemented this phase

- **Seven additional source-inspired, independently written bounded optimizers:** shifted Halton quasi-Monte Carlo, projected finite-difference inverse BFGS, rank-μ full-covariance evolution strategy, RBF Gaussian-process Bayesian expected improvement, artificial bee colony, harmony search, and an adaptive UCB1 operator bandit.
- Combined **19 actual executable optimizers** (12 v1.9 + 7 v2.0). The separately registered **250,000 experiment configurations** remain parameterized combinations, **not** 250,000 distinct implementations or original inventions. No third-party code was copied.
- New `evolution_umbra_tournament_v20.py` creates seven source-hashed research proposals using the new optimizers and passes independent v1.9 synthetic replay. The existing `umbra_evolution_bridge.mjs` performs **separate validation against the actual UMBRA v5 simulation** during GitHub CI. Optimize on toy metrics, never on the UMBRA engine itself; fitness does not demonstrate real-world policy value.
- **Fenced multi-process scheduler:** unique lease identity per invocation, wall-clock lease expiry (unless a test-specific clock is injected), exact-once completion with SQL uniqueness enforcement, active lease counters, bounded selection of qualified **previous-hour** peers. Do not treat same-hour observations as independent collaboration. Four-process test completes 128 distinct jobs with zero collisions.
- **Portable, no-network archive recovery:** `evolution_archive_recovery_v20.py` checks exact segment sizes and SHA-256, rejects traversal/symlinks/unknown members and duplicate names, validates ZIP CRCs, streams the 658MB SQLite database's SHA-256, and can run read-only `PRAGMA integrity_check` plus actual record counts. It refuses to overwrite existing output; never executes archived code or loads weights.
- The live three-part private MYRIAD archive was verified end-to-end: 126,178,612-byte ZIP with SHA-256 `9b59300f52273641cc9fa82914d3b64620e5679a36c791aaa3b752032bafccf6`; SQLite `997eeb993681f37738deb59e334d861e45a965d6fe5ce033684f07d448e6d6d3`, 658,657,280 bytes; actual `390,000` research records from `195,000` identities, SQLite integrity `ok`. **A digest is not a cryptographic signature.** These are synthetic research receipts only.

## Proven method families / references

- Halton: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Halton.html (we use a simple shifted Halton sequence, not SciPy's full scrambling algorithm).
- Quasi-Newton BFGS: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html (projected finite differences and inverse-Hessian update).
- Full-covariance rank-μ evolution strategy: https://github.com/CMA-ES/pycma (simplified original rank-μ adaptation, explicitly **not canonical CMA-ES**).
- Gaussian-process expected improvement: https://proceedings.mlr.press/v306/pion26a.html (small bounded RBF GP with Cholesky solves; no fitted real model or production application).
- Artificial bee colony: https://pmc.ncbi.nlm.nih.gov/articles/PMC3948480/
- Harmony search: https://www.sciencedirect.com/science/article/pii/S0898122112004907
- UCB1 operator allocation: bounded implementation using a four-operator local research bandit, no live feedback loop or market reward.

## Quantitative evidence and limitations

The local benchmark executed **105 synthetic cases**, seven optimizers × five mathematical tasks × three random seeds, capped at 48 objective calls each. Across these tests, **104/105** improved over the center baseline, with no case worse than baseline (a best-so-far evaluator always preserves the center). This is **not** out-of-domain generalization, profitable trading, measured ability training, or meaningful general intelligence.

These seven methods do not independently train MYRIAD's original 8.22 GB agent bank or 640 MB ability bank. Those complete historical raw weights and training ledgers remain missing. The 30 GB/10 GB targets are capacity designs. Neural-weight training during the original ten-agent demonstration must not be counted again.

## Recover the private complete evidence ledger

1. Retrieve from private ChatGPT Library `/MYRIAD-OMEGA/v1.9/two-hour-ledger/` the manifest `MYRIAD_UMBRA_TWO_CYCLE_390000_ARCHIVE_PARTS.json` and **all three** `MYRIAD_UMBRA_TWO_CYCLE_390000_EVIDENCE_LEDGER.zip.partNN` files. Do not commit private archives to public GitHub.
2. Place the manifest and three matching part files in the same directory, unchanged.
3. Run `python scripts/evolution_archive_recovery_v20.py --manifest /path/to/MYRIAD_UMBRA_TWO_CYCLE_390000_ARCHIVE_PARTS.json --sqlite-integrity --report /empty/output/verification.json`.
4. Optional restoration: `--restore-to /path/to/empty/destination` (creates a read-only SQLite file, refuses overwrite). Never point it at live production data.

## Run tests

```bash
python3 -m unittest discover -s tests -p 'test_evolution_archive_recovery_v20.py' -v
python3 -m unittest discover -s tests -p 'test_evolution_algorithms_v20.py' -v
python3 -m unittest discover -s tests -p 'test_evolution_scheduler_v20.py' -v
python3 -m unittest discover -s tests -p 'test_evolution_tournament_v20.py' -v
python3 scripts/evolution_umbra_tournament_v20.py --start 1 --count 7 --budget 32 --output /tmp/v20-candidates.jsonl
node scripts/umbra_evolution_bridge.mjs --input /tmp/v20-candidates.jsonl --output /tmp/v20-worldline-validation.json --limit 7
```

The last command requires the main UMBRA repo source `engine.mjs` and `society.mjs`; this will run in GitHub Actions on the target PR. The local archive contains only the MYRIAD delta files.

## Critical follow-ups

1. Verify exact GitHub Actions status at the current PR head before any merge; no CI result for an earlier commit qualifies a later commit.
2. Train only against physically recovered, checksum-verified original neural-bank bytes and ledgers, not sparse zero-filled allocations.
3. Add auditable parent-receipt links for future peer assimilation. Previous v1.8 same-hour peer records cannot retroactively provide independent prior-hour provenance; their **synthetic receipt-integrity audit is valid but does not certify causal peer learning**.
4. Independent out-of-sample domain evaluation, resource/cost calibration, tenancy isolation, persistent hosted runtime, secured iPhone connectivity and ICARUS research-only adapters still require evidence and explicit authorization.
