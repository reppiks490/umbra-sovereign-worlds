# MYRIAD Ω × UMBRA — v2.3 portable checkpoint verifier

**Status:** research-only, draft PR #21. No new model training, market integration, automated promotion, external inference, large source-bank restoration, or live deployment.

## Scope and before/after

`myriad_bank_fabric.verify_sample` previously checked the hashes for only *listed* agent receipts and ability blocks. An intact `agent_weights.fp16` could therefore be paired with a manifest listing three of ten agent rows, or an ability manifest covering only 2,000 of 10,000 adapters, and still be treated as a verified sample. Duplicate ZIP members and `auto_promote: true` were not rejected. That is an evidence-coverage bug, not a neural-network failure.

The v2.3 implementation verifies **exactly four canonical ZIP entries**, upper-bounded manifest size and exact buffer sizes, full-bank SHA-256 digests, all ten ordered/unique agent receipt identities and positive declared step counts, complete non-overlapping ability range coverage from adapter 1 to 10,000, nonzero ability step bytes, every range/step SHA-256 digest, strict integer and shape metadata, absence of unexpected ZIP content, and explicit `auto_promote: false`. Duplicate JSON keys are refused.

The verifier deliberately returns `training_provenance_independently_attested: false` and carries the self-described source import status. Matching bytes and self-contained hashes are **not** a trusted external signature or proof the file was trained on real tasks. The historical 8.22 GB agent/640 MB ability full banks and original ledgers remain missing. Expanded 30 GB/10 GB capacities are designs, not trained weights.

## Reproducibility

The committed unittest file `tests/test_myriad_bank_verifier_v23.py` builds a small **fully self-contained synthetic checkpoint with exactly the same dimensions**, so public CI never downloads or publishes private user weight bytes. The tests cover missing/duplicate agent records, booleans as indices, unsorted and zero-step rows, range gaps/overlaps/missing/reversed records, invalid digests, wrong shapes, unknown/duplicate ZIP members, duplicate JSON fields, and unauthorized auto-promotion.

```
python3 -m unittest discover -s tests -p 'test_myriad_bank_verifier_v23.py' -v
python3 -m unittest discover -s tests -p 'test_evolution_fabric_v18.py' -v
python3 -c "import json,hashlib,pathlib; m=json.loads(pathlib.Path('research/EVOLUTION_V18_SOURCE_MANIFEST.json').read_text()); assert all(hashlib.sha256(pathlib.Path(k).read_bytes()).hexdigest()==v['sha256'] for k,v in m['files'].items())"
```

Independently, the private saved ten-agent/10,000-ability checkpoint from `/MYRIAD-OMEGA/v1.6/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip` was read through the new verifier in a local test host. The output identifies its 10 imported agent rows as **`imported_unverified`**; adapter step bytes and embedded hashes matched the archived manifest. **The private ZIP must not be committed to GitHub.**

## Next engineering gate

After this passes independent GitHub Actions CI, apply a bounded checkpoint-provenance contract to a **new immutable research artifact**, then implement verified independent holdout model evaluation before connecting any work to a hosted model. Validate source authority separately from source-byte consistency. Maintain user-approved 13/13 MYRIAD release criteria and no automatic ICARUS merges.

**Knowledge delta:** `scripts/myriad_bank_fabric.py`, `tests/test_myriad_bank_verifier_v23.py`, `docs/EVOLUTION_V23_CHECKPOINT_VERIFICATION.md`, `research/EVOLUTION_V18_SOURCE_MANIFEST.json`, `research/EVOLUTION_V23_SOURCE_MANIFEST.json`, `.github/workflows/myriad-bank-verifier-v23-ci.yml`.
