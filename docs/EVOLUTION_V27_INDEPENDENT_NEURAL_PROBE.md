# MYRIAD Ω × UMBRA Ω — v2.7 Replayed neural inference on fresh synthetic inputs

**Research-only; no broker/trading authority, production promotion, automatic model operations or pretrained-model provenance attested.** The model weights are saved private from v2.5 and remain unchanged.

## What is genuinely new

The v2.5 synthetic curriculum produced ten FP16 neural network candidates (411,000 parameters each) and an adapted bank of 10,000 FP16 32-parameter vectors. The v2.7 `scripts/evolution_neural_probe_v27.py` *loads those saved FP16 parameters* and executes CPU PyTorch network inference on deterministic **new input samples with seeds 900000 and 900001**. None of the probe input generators generated the v2.5 training or prior-holdout rows; the original teacher function and mathematical task family are unchanged. This is novel-input generalization within one synthetic task family, **not distribution-agnostic transfer, trading edge, or general intelligence.**

For each agent and probe seed, run 96 standard and 96 shifted-input examples. For the 10k adapter bank, run two fresh 32×30 projection test matrices per seed. Compare the original preserved FP16 checkpoint with v2.5 trained FP16 candidates, quantify mean squared error, and record SHA256 of every original, candidate, and probe-input tensor. Both sources are checked against the archived v2.5 training ledger. The private candidate files remain in `/MYRIAD-OMEGA/v2.5/` and are not committed to GitHub.

## Audited actual result

See `research/EVOLUTION_V27_INDEPENDENT_NEURAL_PROBE_SUMMARY.json`. Each of the ten candidate agents outperformed its source on **all four new agent tests** (standard/shifted at 2 independent-input seeds), and the candidate ability bank outperformed its source on all four new ability tests. Two complete replay attempts reloaded the saved FP16 weights and recomputed the report. Three adversarial trials rejected a **re-sealed forged score**, a **re-sealed forged model hash**, and **tampering with a copied candidate weight file**. The report's source import status remains `imported_unverified`.

Integrity of a saved model artifact is different from independently attested *original training history*; replaying a synthetic function is different from real-world generalization. The original complete 8.22GB + 640MB historical weight banks and ledgers are still missing. The 30GB and 10GB proposed expansions do not contain trained full models.

## Reproduce with private files locally

Requires CPU PyTorch and NumPy, the authentic `MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip` source archive, and the **private v2.5 trained candidate directory**.

```bash
python3 -m unittest discover -s tests -p 'test_evolution_neural_probe_v27.py' -v
python3 scripts/evolution_neural_probe_v27.py run --archive /private/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip --candidates /private/v25_candidates --receipt /private/v27-receipt.json --seed 900000 --authorize
python3 scripts/evolution_neural_probe_v27.py verify --archive /private/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip --candidates /private/v25_candidates --receipt /private/v27-receipt.json
```

`run` is exclusive-write (never overwrites evidence); `verify` replays *all ten* saved models and the complete 10,000-adapter bank from original bytes. Saved reports are ordinary SHA256 integrity records, not external signatures. Public CI exercises the 9 source-only adversarial checks without downloading private models. The full private FP16 replay was run locally and its private receipts are preserved in ChatGPT Library `/MYRIAD-OMEGA/v2.7/`.

## Boundaries and continuation

- Keep research changes on draft PR #21. NO merge to UMBRA main or ICARUS OMNIGENESIS PR #503 until independent MYRIAD 13/13 release gates and explicit owner approval.
- Never expose private checkpoints, user credentials or live broker activity in a public repo or website.
- Next engineering targets: independent training-domain datasets, real out-of-distribution model evaluations, pinned external model + dataset licenses, signed checkpoint lineage, and a no-auto-enroll, resource-budgeted execution path to v2.6 workers.
