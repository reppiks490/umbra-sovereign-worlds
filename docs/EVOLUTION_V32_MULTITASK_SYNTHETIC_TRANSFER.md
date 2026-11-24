# MYRIAD Ω v3.2 — ten saved FP16 agents, constrained multi-task composition

**Research-only.** This runs real CPU PyTorch backpropagation on the ten previously saved **411,000-parameter** neural networks from a private v2.5 training archive. It does **not** modify the v2.5 archive, update the 10,000 ability adapters, verify historical training ancestry, certify market value, deploy an inference model, or authorize release/merges.

## Experiment design

All sources have explicit SHA-256 integrity checks. Every trained model sees **2,048 synthetic observations with three task-factor sign patterns** (a, b, c signs same/same/same, same/opposite/same and same/same/opposite). A fourth combination (same/opposite/opposite) is *withheld* for a composition transfer check. Separate seed streams create the source, trained holdout and new task function. The model receives the task descriptors as inputs. **The withheld composition uses the same teacher operator basis** as training, so it is not evidence of wholly new knowledge.

A second falsification control changes the synthetic target function to include a cubic term, sine and tanh. The trained model has **not trained on this exact target expression**, although nonlinear basis functions and features overlap. Report these as limited mathematical transfer, not general reasoning or independent OOD market intelligence.

The three baselines are original v2.5 parameters, zero-output, and `a*z` linear-only prediction. An agent earns a private research-review-eligible flag only if the quantized FP16 file beats *both* zero-output and linear-only on the withheld sign composition **and** changed function. A research-review flag never becomes production authorization.

## Real local results (seed 20261124, 220 gradient steps for each of ten networks)

| Heldout task | Mean v2.5 source MSE | Mean v3.2 FP16 MSE | Mean zero MSE | Mean linear MSE | Trained beat both simple baselines |
|---|---:|---:|---:|---:|---:|
| Same teacher / fresh seed | 4.40617 | 0.57671 | 4.06168 | 1.53221 | 10/10 |
| Blind double-opposition composition | 4.13747 | 2.94551 | 3.74354 | 3.27284 | **10/10** |
| Changed cubic/trigonometric function | 11.85784 | 3.96734 | 11.39744 | 4.60679 | **10/10** |

Private source archive and all ten trained FP16 files were reloaded in a separate verification invocation; the results were independently recomputed with exact deterministic input seed streams. A changed candidate byte, a re-sealed false metric and a re-sealed forged source SHA-256 were rejected. Four private-weight tests passed plus eight source tests.

**Critical limitations:** This is a tiny deterministic synthetic test, with no real labels, market outcomes, independent model attestation, execution on the user's PC, actual downloadable model-service deployment, or general-purpose intelligence proof. The training source v2.5 parameters had **unverified original historic training ancestry**. Fine-tuning and valid SHA256 checks do not replace source provenance.

## Reproduce

```bash
python3 -m unittest discover -s tests -p 'test_evolution_multitask_v32.py' -v
python3 scripts/evolution_multitask_v32.py train --archive /private/MYRIAD_OMEGA_v2.5_PRIVATE_TRAINED_SYNTHETIC_CANDIDATES.zip --out /private/new-v32-dir --agents 10 --steps 220 --seed 20261124 --authorize-synthetic-training
python3 scripts/evolution_multitask_v32.py verify --archive /private/MYRIAD_OMEGA_v2.5_PRIVATE_TRAINED_SYNTHETIC_CANDIDATES.zip --out /private/new-v32-dir
```

Private case-specific tests: `python3 -m unittest discover -s tests -p test_evolution_multitask_v32_private.py -v` in the environment with original private archives. GitHub CI **does not** hold private source or candidate bytes and executes only source-level safety qualification. No secrets or full raw training source in the public repo.

## Next independent gates

1. New teacher families unrelated to the deterministic synthetic generator, with labels from authenticated external datasets and strict time/asset splits. An unfitted zero and meaningful domain baselines must be preregistered.
2. Integrate byte-verified artifacts through `evolution_artifact_registry_v29.py`, binding exact model version and original v2.5 source archive.
3. Cross-run reproducibility on user-authorized PC or bounded external executor, auditing compute, model quality and cost.
4. MYRIAD 13/13 independent acceptance gates and explicit owner review before UMBRA/ICARUS model promotion or any trading authority. Never schedule Codex.
