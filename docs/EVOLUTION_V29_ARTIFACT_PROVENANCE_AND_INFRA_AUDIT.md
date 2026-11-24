# MYRIAD Ω × UMBRA — v2.9 private artifact registry and observatory build audit

**Research-only on draft PR #21. No merging into UMBRA main, no ICARUS changes, production deployment, broker execution, or scheduled Codex.**

## Security problem addressed

The verified v2.5 private source contains ten FP16 agent candidate files, one FP16 10,000-adapter candidate file and two metadata receipts. The preceding tasks correctly checked most hashes, but the weight cohort did not yet have a single **strict, signed, refuse-extra-files registry**. Opaque filename-based loading is vulnerable to accidental replacement, registry partial coverage, unsigned local metadata and mistaken claims of source origin.

### v2.9 behavior

- `scripts/evolution_artifact_registry_v29.py` inventories all files in one **flat private directory**. Exactly 256 or fewer items, <=2GB per file and <=12GB total (pilot caps). Explicit authorized creation and an exclusive new receipt path.
- The registry records the exact byte length, SHA-256 and format for every allowed `.fp16`, `.safetensors` and `.json` file. Files are streamed rather than fully copied into RAM, and the verifier rejects extra, missing, renamed or modified files, folders, dangerous filenames, symlinks, malformed JSON and nonfinite JSON literals. Binary `.fp16` files must contain an even number of bytes.
- `.safetensors` receives a strict **subset** structural validation: bounded JSON header; duplicate keys rejected; dtype, shape, data offsets, non-overlapping fully indexed payload checked. It is a limited pilot validator, not an alternative implementation certified equivalent to the official library. No tensor deserialization or pickle is performed.
- The receipt is sealed with **HMAC-SHA256** using a separate owner-provided `MYRIAD_ARTIFACT_REGISTRY_KEY` (>=32 characters) that must remain private. This authenticates the integrity of local evidence **only relative to custody of the secret**. A checksum alone does not prove the identity, training history, license or origin of external weights. Never share the key alongside the registry. If the key is unavailable later, `verify` correctly refuses to claim authentication.
- Local sources are labeled `imported_unverified`, and pinned external-model references require a **40-character full immutable Git revision** but still carry `model_origin_authenticated=false` until an independently verified Hub API/file-digest comparison is performed. Declared licenses are recorded but **not automatically authenticated**. No network download or billable inference is triggered by this tool.
- Hard prohibition in source and tests on `production_authority`, `automatic_promotion`, falsely verified license or model-origin flags. Owner release gates remain closed.

### Actual private cohort acceptance test

On an isolated local candidate directory, the registered v2.5 source had **13 files**, totaling **8,868,357 bytes** (11 FP16 weight files + training report and private audit). HMAC registration and an independently re-read verification succeeded, a single-byte perturbation of a candidate was rejected, and subsequent restoration of the original bytes re-verified successfully. The test used a temporary randomly generated key **not committed to GitHub**. This is a local integrity demonstration; future authentication needs the owner-supplied key.

```sh
export MYRIAD_ARTIFACT_REGISTRY_KEY='a-separate-owner-managed-secret-at-least-32-characters'
python3 scripts/evolution_artifact_registry_v29.py register \
  --root /private/v25-candidate-directory \
  --manifest /private/v29-signed-manifest.json \
  --model-id myriad-v25-private --source imported_unverified \
  --license-id unknown --authorize
python3 scripts/evolution_artifact_registry_v29.py verify \
  --root /private/v25-candidate-directory \
  --manifest /private/v29-signed-manifest.json
```

Public, fixture-only tests (no private bytes, key or paid API calls):

```sh
python3 -m unittest discover -s tests -p 'test_evolution_artifact_registry_v29.py' -v
```

### Railway observatory deployment failure — verified read-only audit

A connected Railway API inspection found project **MYRIAD Evolution Observatory**, service `evolution-observatory`, on environment `production` with latest deployment `ec6c91ef-f3b4-4442-af4f-ceb98220165c` **FAILED**. This deployed from UMBRA **main**, commit `7cb56801795b1f9bc590a9ec1bc3ffeadab7362f`. The failure stage was `BUILD_IMAGE`, builder **RAILPACK**, with no start command. Actual Railway build log states **“No start command detected”**. A custom Dockerfile exists in the research source at `evolution/Dockerfile` and the service configuration reports that path, but **the builder was still RAILPACK**. The build never reached application startup or its `/api/health` check.

**Safe operator repair plan (NOT performed):** Confirm the correct Railway service/workspace; change its builder to **DOCKERFILE** using `evolution/Dockerfile` at the authorized commit, verify start command and correct `PORT` binding, then use a preview/staging deployment and confirm a successful `/api/health` response before any production promotion. Do not use unrelated provider credentials or unbounded cloud instances. This remains **blocked by MYRIAD release gate and explicit owner approval for production deployment**; no service settings were changed by v2.9.

**Up-to-date Railway context:** `railway.json`/`railway.toml` Config as Code is deprecated as of this audit, with a documented 2026-12-01 migration cutover; do not create a new legacy configuration. Prefer the new Railway Infrastructure as Code and service-specific settings for the eventual authorized repair. Source: [Railway Config as Code](https://docs.railway.com/config-as-code/reference), [Dockerfile builds](https://docs.railway.com/builds/dockerfiles), [Infrastructure as Code](https://docs.railway.com/infrastructure-as-code/reference).

### Next acceptance gate

Try one **authorized, pinned and independently hashed** open model via Hugging Face and CPU-only isolated inference, then measure true cost, latency and output correctness using v2.4 evidence and v2.6 worker leases. Future training requires training/evaluation task separation and a comparator beating zero; v2.8 found 0/66 cross-task wins. Do not conflate a pinned revision or HMAC with independent model identity provenance. Original historic large 8.22GB / 640MB banks and their ledgers remain missing.
