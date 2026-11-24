# MYRIAD v4.0-v4.1 ? teacher supervision and semantic source retrieval
The existing Qwen3 8B digest is pinned to the observed local tag. Inference is
admitted only when no model is resident and at least 6200 MiB physical and
7500 MiB virtual memory are free. A separate, experimental third-party compressed
8B IQ2_M artifact is allowed only after local digest pinning and an exclusive
4700 MiB physical / 7500 MiB virtual memory check. These are conservative
admission thresholds, not guarantees. The original model remains intact.
Granite4 350M and DeepSeek-R1 1.5B are teacher qualification candidates, not
automatic production replacements. Qwen3 1.7B is a small-model fallback.
Teacher responses on four deterministic synthetic admission-rule families are
independently scored. Wrong labels are discarded. A tiny 9-parameter logistic
student may be gradient-trained after 24 unique accepted examples, evaluated on
separate generated seeds; this is not LLM weight fine-tuning or market training.
MiniLM 22M provides actual local embeddings and ranked, hash-bound code retrieval.
Retrieval is not a certified search benchmark or automatically injected instruction.
The serialized five-minute scheduler reserves one teacher window per hour,
one alternating small-teacher/retrieval window, and ten worker windows.
Private receipts stay local, HMAC-sealed; no external data transfer or promotion.
Hardware capacity, download completion, actual teacher calls and sustained throughput
must be measured separately from registration and source qualification.
