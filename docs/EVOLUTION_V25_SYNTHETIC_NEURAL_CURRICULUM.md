# MYRIAD Ω × UMBRA — v2.5 two-regime neural training experiment

**Research-only, no automatic model promotion, trading or ICARUS merge.** This is an opt-in CPU PyTorch training experiment on the preserved **ten-agent / 10,000-adapter sample**, not the missing original complete 8.22 GB/640 MB banks or the proposed 30 GB/10 GB expansions.

## What ran on the private test host

1. Load the actual preserved checkpoint `MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip` through the strict v2.3 verifier, including exact row and ability range hash/step receipt coverage. The saved checkpoint's `agent_rows_imported_as` is **`imported_unverified`**. This input status remains visible in all output manifests.
2. Reconstruct each of the ten 411,000-parameter `32 → 512 → 544 → 208 → 8` PyTorch policies from the archived FP16 weights. Train each in two deterministic **synthetic** stages: 16 updates on a base task and 16 on a shifted input regime. Use the saved ability vectors as a bounded numerical context, without silently modifying the source archive.
3. Train the entire preserved **10,000 × 32-parameter** ability array using real vectorized PyTorch autograd for 16 updates on each of two synthetic feature regimes. The training objective uses a deterministic mathematical teacher unrelated to market, language, or real-world expertise.
4. Save ten separate FP16 policy candidates and one 640,000-byte FP16 ability candidate into a **private quarantine directory**, alongside SHA-256 lineage receipts and measured IID/shifted holdout losses. Reload the quantized weights before evaluating final losses.
5. Independently run the `verify` command on those saved bytes, which reopens the original archive, verifies every source and candidate row hash, rebuilds every synthetic holdout from the recorded seed and the original ability context, independently recomputes all 22 holdout comparisons and rejects changed metrics or claimed improvements not reflected by the saved weights.

### Exact measured experimental results

- **10/10** candidate policies improved their independently generated IID synthetic holdout MSE.
- **10/10** candidate policies improved their shifted-input synthetic holdout MSE.
- Full candidate 10,000-adapter bank IID holdout MSE **0.9372742176 → 0.6732832789**.
- Full candidate 10,000-adapter bank shifted-input holdout MSE **1.5511494875 → 0.9510032535**.
- No original checkpoint overwrite, and **no model deployment, finance evaluation, live trading, or new full 30 GB/10 GB trained bank**.

The source checkpoint may contain metadata that describes prior synthetic training, but the source's training provenance is **not independently attested**. Improvements demonstrate that **the actual saved parameters underwent gradient optimization on these generated tasks only**. They do not imply profitable trading, language-model reasoning, independent intelligence, or transferable production capabilities.

### Reproduce locally (requires PyTorch and NumPy)

```sh
python3 scripts/evolution_neural_curriculum_v25.py plan
python3 scripts/evolution_neural_curriculum_v25.py train --archive PRIVATE_PRESERVED_CHECKPOINT.zip --out PRIVATE_EMPTY_QUARANTINE_DIR --agents-count 10 --steps 16 --seed 1337 --authorize-synthetic-training
python3 scripts/evolution_neural_curriculum_v25.py verify --archive PRIVATE_PRESERVED_CHECKPOINT.zip --out PRIVATE_EMPTY_QUARANTINE_DIR
```

The verifier refuses a changed source, changed candidate byte, changed source row digest, and a re-sealed false holdout metric. These checks ran locally against the real 8.86 MB private candidate output. The public GitHub CI does **not** receive the private weight files and checks only code import/CLI plan and safety preconditions. **Do not describe public CI as independently having run PyTorch training.**

### Private artifact preservation

Keep all candidate weights, full numerical report, and adversarial audit in the user’s private Library at `/MYRIAD-OMEGA/v2.5/`; do not commit raw weights or raw private archive bytes to GitHub. The public report `research/EVOLUTION_V25_TRAINING_SUMMARY.json` contains aggregate numerical outcomes only and honest evidence flags.

### Remaining gates

Original full historical weights/ledgers missing. No owner-approved production model provenance, license verification, independently held-out real market data, walk-forward real-fill evaluation, always-on 195,000 neural-process fleet, secure cloud deployment, or MYRIAD 13/13 release criteria. Continue on the draft branch until explicit owner approval.

**Knowledge delta:** `scripts/evolution_neural_curriculum_v25.py`, `tests/test_evolution_neural_curriculum_v25.py`, `docs/EVOLUTION_V25_SYNTHETIC_NEURAL_CURRICULUM.md`, `research/EVOLUTION_V25_TRAINING_SUMMARY.json`, `research/EVOLUTION_V25_SOURCE_MANIFEST.json`, `.github/workflows/myriad-neural-curriculum-v25-ci.yml`.
