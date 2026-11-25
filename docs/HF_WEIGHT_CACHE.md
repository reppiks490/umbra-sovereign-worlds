# HUGGING FACE WEIGHT CACHE — UMBRA Ω

Public Hugging Face model repositories serve as a remote source of reproducible original native weights, not a private backup service. The cache retains the acquisition receipt, model revision, SHA-256, license, tokenizer/config and experience records when the owner explicitly evicts an eligible model's original model.safetensors file. The remote registry shows the model as remote (not locally executable). All other files are left untouched. No user data, learned weights or credentials are uploaded.

Eviction requires matching the complete local receipt and exact original weight hash, then checking the pinned public, ungated Hugging Face revision, license, byte size and LFS digest. Modified, unavailable, gated, private, missing or ambiguous artifacts fail closed. Only single-file native safetensors acquired in the existing neural/tiny receipt layout are supported; no automatic eviction, Ollama/GGUF/sharded checkpoint deletion or removal of trained weights. A public repository can disappear or become inaccessible; use separate backups for irreplaceable artifacts.

Owner-local CLI, using the reviewed Python venv:
- python scripts/hf_weight_cache.py --root PRIVATE_MODEL_ROOT list
- python scripts/hf_weight_cache.py --root PRIVATE_MODEL_ROOT evict EXACT_SHA256
- python scripts/hf_weight_cache.py --root PRIVATE_MODEL_ROOT ensure EXACT_SHA256

The root's acquisition lock and inference-use lock prevent cooperative concurrent mutations. A live acquisition job blocks eviction and restoration; never manually remove an active lock. Restoration checks remote metadata, streams into a separate staging file, verifies SHA-256 and native floating-point layout, and retains at least 8 GB free (5 GB Windows + 3 GB learning workspace). There is no automatic purge to make room. This reserve is a minimum, not a separate partition or guaranteed free capacity.

The owner-configured native catalog exposes archived entries with availability=remote and weights_verified=false. Setting UMBRA_AGENTIC_AUTO_RESTORE=1 explicitly enables on-demand restoration of one unambiguous supported BERT model before its native inference; otherwise restore through the CLI. Configure UMBRA_AGENTIC_NATIVE_ROOT and UMBRA_AGENTIC_NATIVE_PYTHON as described in AGENTIC_NEXUS.md. Unsupported families remain catalog-only until adapters exist. No external-model inference API, private Hub repository, scheduled task, or upload is configured. Qwen3.8 Ollama download and existing installed models are outside this cache scope.

Tests: npm test; Python unittest discovery for test_hf_weight_cache.py and test_agentic_native.py. Cache tests cover exact round-trip, preserved receipts, changed weights/source, acquisition lock, failed restore and reserve; Node tests cover truthful remote inventory. Tests use isolated fixtures. Live public-weight proof is separate from the production queue.

Verified live round trip: ibm-granite/granite-timeseries-ttm-r2 revision d6a79570cac0f33d526601cd3a0fc7c80a8f9a2f, 3,240,592 bytes, SHA-256 a706726a7eb01bbcb42994b7dcb3c06ea9557898dbae8d480eb04fe8ccb89710. Initial restoration, explicit eviction, remote-only registry status and identical restoration succeeded in an isolated disposable test directory. No production weights removed. Full Node suite 120/120; HF cache Python tests 5/5; native inference Python tests 3/3. This verifies weight transport, not model inference.
