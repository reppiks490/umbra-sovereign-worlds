# AUTOGENESIS Ω v0.1 — synthetic adaptive laboratory

This subsystem is a bounded, reproducible policy-learning experiment over the existing UMBRA synthetic world. Ten role families define 100 distinct policy strategies, not 100 independently trained neural agents. Each observation records an actual paired-seed simulator evaluation and audit. UCB selects exploration candidates, deterministic mutation provides challenger policies, a small learned linear reward predictor contributes to challenger ranking, and eight unseen paired holdout worlds determine promotion (positive mean and at least six positive differences). The incumbent is retained if the gate fails. No real-world causal or scientific qualification is claimed.

Reward is a chosen synthetic utility combining log population, log food/water, knowledge, infection, carbon, biodiversity and inequality. This is an arbitrary engineering objective, not welfare science. Training uses one paired observation per candidate and can overfit; holdout is an internal check, not independent empirical evidence. The checkpoint SHA-256 detects accidental corruption, not hostile authorship. Checkpoints are trusted local operator files only.

## Use
- Owner stdin: {"operation":"autogenesis_roles"}.
- Owner stdin: {"operation":"autogenesis_run","arguments":{"seed":49021,"rounds":16,"steps":12}}.
- Persistent experiment: node scripts/autogenesis_train.mjs PATH 49021 16 12. PATH is an operator-owned private checkpoint outside the repository; reuse the same seed and steps on continuation. Maximum cumulative training observations: 512. Maximum 100 rounds and 120 steps per invocation. Use one writer per checkpoint.
- Run npm test for the full Node regression suite.

POLYMIND's existing memory admission is reused for advisory model routing. Qwen3.8:27b-q8_0 is allowlisted as a senior advisory model only if actually installed and sufficient free physical memory exists. This PC has roughly 16 GB RAM and cannot pass that model's present memory gate. No swap-based override is introduced.

The separate owner-local acquisition process is queued behind Q8 and is not part of this repository change. Native safetensors inference, actual neural weight fine-tuning, agent debate, knowledge distillation, learned tool routing, real continual learning benchmarks and integration of acquired model weights remain unimplemented. The roles are strategy configurations; the only weights trained here are a small numerical linear predictor. No automatic real-world actions, deployments, tool execution, or scheduled job modifications.
