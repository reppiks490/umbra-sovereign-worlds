# MYRIAD Ω × UMBRA — v2.8 independent target-function tribunal

**Status:** experimental source on draft PR #21 only. No main merge, broker authority, neural promotion, missing historical-bank recovery, or Codex in scheduled tasks.

## Why v2.8 exists

v2.5's real PyTorch gradient updates improved error on their original seeded synthetic mathematical function. v2.7 used fresh input samples, **but kept the same teacher function**. This verifies interpolative generalization within a task, **not** general-domain transfer. v2.8 tests that assumption by fixing three new target families before seeing the results and comparing against both the original source weights and a **zero-output baseline**. The result may be negative: a trivial model may beat trained weights on unrelated targets.

## Preregistered test protocol

- Dataset seeds: **980004, 980005**, fixed in code, and cannot equal the v2.5 training seed or the v2.7 probes.
- Subjects: **10 exact original 411,000-parameter FP16 neural networks**, **10 saved FP16 trained candidates**, the full original/saved **10,000 × 32 FP16 ability adapter bank**. Every candidate is checked against v2.5 source and training receipt SHA-256 metadata, the preserved original checkpoint, and its expected byte extent.
- Three fixed synthetic teacher families for both agents and ability adapters: `antipodal` reverses the original teacher, `nonlinear_interaction` tests out-of-family nonlinear interactions, and `independent_linear` uses a separately seeded teacher unrelated to original training.
- Agent inputs: 112 new deterministic examples per agent per seed. Ability inputs: 32 × 12 fixed independent projection values per seed. Targets remain deterministic mathematical synthetic tasks—not real market prices, text cognition, model-instruction following, or unseen external empirical datasets.
- Metrics: MSE for source, trained candidate, **and zero output**. A meaningful signal must beat **both** comparators. The three-family, two-seed plan is immutable in source. No post hoc task selection or automatic promotion.
- Receipts: private JSON with SHA-256 seal, source identity, candidate and target hashes, all per-subject scores. The `verify` command independently reloads every saved FP16 checkpoint and recomputes **all 33 cases/seed** with near-equal float tolerances, rejecting altered metrics or source bytes. A local checksum detects modification but **does not authenticate the author**.

## Actual result — negative transfer evidence

All results below are **real inference on saved PyTorch FP16 network weights**, not mock models. Two separately seeded receipt files were independently replayed from original/candidate checkpoints.

| Seed | Families | Agent comparisons | Ability-bank comparisons | Candidate wins vs original | Candidate wins vs zero | Wins vs both |
|---|---:|---:|---:|---:|---:|---:|
| 980004 | 3 | 30 | 3 | 9 | **0** | **0** |
| 980005 | 3 | 30 | 3 | 9 | **0** | **0** |
| **Total** | **3** | **60** | **6** | **18** | **0** | **0** |

Every run includes complete per-case source, trained, and null MSE. The candidate weights were **not** universally superior to original checkpoints; the opposite-teacher tasks showed clear negative transfer. The formal result is not “no learning” but **“no evidence of cross-task advantage beyond the zero predictor in this predeclared suite.”** The result falsifies a claim that v2.7 already demonstrated useful independent-task generality. It does not prove that all future tasks will be failures.

## Reproduce

For cheap, public, dependency-light behavior checks:

```sh
python3 -m unittest discover -s tests -p 'test_evolution_transfer_ood_v28.py' -v
```

For *private* real FP16 replay (requires locally restored private 10-agent sample and candidate archive; do not upload these to public GitHub):

```sh
python3 scripts/evolution_transfer_ood_v28.py run \
  --archive /private/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip \
  --candidates /private/synthetic-v25-candidates \
  --receipt /private/transfer-v28-seed980004.json --seed 980004 --authorize
python3 scripts/evolution_transfer_ood_v28.py verify \
  --archive /private/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip \
  --candidates /private/synthetic-v25-candidates \
  --receipt /private/transfer-v28-seed980004.json
```

Second preregistered seed `980005` follows the same process. Candidate directory includes the **original saved FP16 candidate files** plus `SYNTHETIC_TRAINING_REPORT_V25.json` extracted from the private archive. Output receipts are non-overwriting and quarantine-only.

## Follow-up engineering and promotion gates

1. Train **multi-task** rather than single-teacher candidates; use honest training/validation/test task separation and blocked evaluation seeds. Compare with zero, source, random initialization and trivial task-aware baselines; report all losses and costs.
2. Add task-disjoint ability adapter cohorts, train-only/held-out task family labels, and source immutable revision SHA plus sample hashes to the research registry. Ensure no source sample text or sensitive provider tokens is in Git.
3. Conduct a real benchmark from an independently licensed, appropriately isolated external dataset with leakage screening, evaluator versioning and blind test splits. In-sample mathematical task mastery is not market edge.
4. Before production, separately verify real model identity, authenticated inference, persistent fleet throughput under budget, and 13/13 owner-approved release gates. No continuous remote worker fleet or trained 30GB/10GB banks exist today.

**Independent related research:** [DataSAIL similarity-aware splitting (Nature Communications, 2025)](https://www.nature.com/articles/s41467-025-58606-8), [Kernel Divergence contamination analysis (ICML 2025)](https://proceedings.mlr.press/v267/choi25b.html), and [Hugging Face safetensors format](https://github.com/huggingface/safetensors/blob/main/README.md). These sources support *methodological considerations*, not the reported local neural MSE values.
