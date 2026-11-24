# MYRIAD Ω — v2.4 independent model-evaluation evidence

**Review-only in UMBRA PR #21; no live trading, automatic promotion, or model training.** Extends the opt-in loopback-only v2.2 model evaluation without modifying its existing API or changing the 195,000 synthetic workflow scheduler.

## What this implements

- Fixed localhost model endpoint through the v2.2 adapter, with explicit `--authorize`, local bearer token in `MYRIAD_LOCAL_MODEL_TOKEN`, no redirects, at most eight toy arithmetic tasks and 64 requested completion tokens each. Provider-reported token usage is **not** an independently audited billing quantity.
- Separate private `MYRIAD_EVIDENCE_HMAC_KEY` (32–256 printable ASCII characters) authenticates each evidence receipt. Neither key is stored in source or output. Store keys in a secure OS secret store, not an environment file committed to Git. The HMAC permits third-party integrity checking only when the verifier is given the trusted key; a key-holder can still forge a receipt.
- The output is an exclusively created, permission-0600 **private JSON receipt** storing actual raw responses to deterministic toy arithmetic questions, expected answers and hashes. `verify` independently regenerates prompts and targets, recomputes exact-match scoring from the retained raw content, verifies per-row SHA-256 and aggregate values, and requires a valid private HMAC. Unlike v2.2's hash-only receipt, a changed output cannot be made to pass merely by changing its `correct` field.
- Invalid endpoint response, excessive output, bad token usage, missing key, wrong signature, exceeded request budget, absence of authorization, or incomplete run fails closed. The total elapsed deadline is checked **between calls**, with each socket request limited to the remaining deadline. This is **not a hard process-kill timer**, and a noncompliant network endpoint can exceed the requested completion-token limit before the client can stop it.
- Zero external API calls in GitHub CI. Dedicated unit tests use deterministic injected transport. The earlier v2.2 CI tests already cover actual localhost HTTP transport via a test fixture. **No real model has been inferred with or trained by this v2.4 change yet.**

## Usage on an authorized local machine

Set both distinct secrets privately and make sure the local inference service implements the v2.2 OpenAI-compatible endpoint and usage fields:

```sh
python3 scripts/evolution_model_evidence_v24.py run --port 11434 --model YOUR_PINNED_LOCAL_MODEL --seed 41 --count 3 --max-tokens 16 --budget 48 --timeout 5 --deadline-seconds 20 --out private-raw-model-evidence.json --authorize
python3 scripts/evolution_model_evidence_v24.py verify private-raw-model-evidence.json
```

Do not publish raw evidence, tokens, or the HMAC key in GitHub. Although the current benchmark is synthetic, **future datasets may contain personal or proprietary data and require encryption and authorized access controls**, not merely file permissions.

## Scientific and release status

- A valid HMAC does not prove the identity of an independently trained model or its artifact SHA-256; both endpoint and model fields remain self-reported. It only validates an untampered receipt under the provided key.
- `score_replayed` means **the saved output was independently re-scored**, not that the model's stochastic generation was reproduced. Actual reproducible model-backed evaluation requires pinned checkpoint artifacts, independently sourced held-out data and repeated executions.
- The original full 8.22GB/640MB neural banks and ledgers are unavailable; the 30GB/10GB targets remain untrained capacity designs. The preserved ten-agent checkpoint's source status is `imported_unverified`.
- The user must independently approve the 13/13 MYRIAD release gates and subsequent production integrations. Do not merge into UMBRA `main` or ICARUS OMNIGENESIS. Scheduled Codex use remains prohibited.

**Knowledge delta:** `scripts/evolution_model_evidence_v24.py`, `tests/test_evolution_model_evidence_v24.py`, `docs/EVOLUTION_V24_PRIVATE_EVIDENCE.md`, `.github/workflows/myriad-model-evidence-v24-ci.yml`, `research/EVOLUTION_V24_SOURCE_MANIFEST.json`.
