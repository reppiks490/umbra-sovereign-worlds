# UMBRA Ω — Sanitized Mastery Receipt Contract (UM-112)

**Scope:** isolated, read-only Node.js projection in `mastery-receipts.mjs`. This contract is for future **world-intelligence evaluation observability**. It is not a model runner, a trainer, an authenticated storage adapter, a production UI, or permission to read private receipts. It does not change `engine.mjs`, `court.mjs`, browser storage, or the live website.

## Data-flow / evidence boundary

1. An existing, separately authorized owner-local lane must produce a **sanitized, pre-reviewed, data-only** receipt batch. Do not copy raw prompts, answers, private identifiers, token-bearing strings, filesystem paths or source datasets into UMBRA.
2. Consumers call `summarizeMasteryReceipts(receipts, {asOf:'2026-11-28T18:00:00.000Z', maxAgeHours:24})`. The UTC `asOf` is supplied explicitly; no clock, network or filesystem side effects occur in this module.
3. Input is an ordinary dense array of at most 1000 exact-key plain-data objects. Unknown, missing, getter, symbol or extra properties are rejected; private data does **not** pass through a permissive serializer.
4. Each `umbra.mastery.receipt.v1` record has exactly these 16 fields:

| Field | Validation |
| --- | --- |
| `schema` | Literal `umbra.mastery.receipt.v1` |
| `model_id`, `source_id`, `evaluator_version`, `question_id`, `attempt_id` | Bounded 1–64-character aliases, restricted ASCII ID grammar |
| `checkpoint_sha256`, `source_sha256` | Lowercase 64-character hexadecimal **declared IDs**, not independently authenticated here |
| `skill` | navigation, event-understanding, state-prediction, planning, resource-management, adaptive-entities, constraint-following, recovery, long-horizon, visual-perception |
| `difficulty` | Integer 1–5 |
| `split` | development, transfer, retention, final-holdout |
| `grade` | pass, fail, abstain |
| `failure_category` | Required for failed grades only: state, causal, constraint, navigation, resource, format, unsupported, uncertainty, other; otherwise `null` |
| `observed_at` | Valid exact millisecond UTC ISO-8601 time, no future-dated record relative to `asOf` |
| `tokens`, `latency_ms` | Finite nonnegative bounded integer observations |

A repeated attempt ID for the same model/checkpoint is rejected rather than double-counted. A question reused across different splits for the same model/checkpoint is rejected to surface possible holdout contamination. Distinct attempts at the same question within one split count once in `uniqueQuestions` and separately in `attempts`. Models and checkpoints remain distinct. The compact summary includes per-skill failures, grade and split counts, highest passed difficulty and source IDs, with `EMPTY`, `STALE` or `READY` display states. This is **not** a claim of skill mastery.

## Provenance and trust limitations

- `inputTrust: UNVERIFIED_SANITIZED_DATA` is always returned: no authentication, independent grader provenance, real inference, fresh source access, source license verification, or checkpoint hash verification occurs here.
- `weightTraining: NOT_EVALUATED` is always returned. A reported evaluation score, arbitrary `weight_training_verified` field, source hash or model label must not become a training or production claim. Actual optimizer activity, candidate digest changes, authentic-source licenses and independent holdouts remain EXASOVEREIGN-owned qualification gates.
- Strict plain-record validation avoids invoking ordinary accessor and `toJSON` fields; it is **not a JavaScript sandbox** against hostile Proxy traps, untrusted executable code, or independently malicious input producers. Accept only authorized, already sanitized data. The aggregator does not provide cryptographic verification or a trusted ingestion endpoint.
- Do not expose final holdout questions/answers to the renderer; only sanitized counts may be supplied. A future observatory must distinguish fixture/demo counts from verified real receipts.
- No persistent store, network fetch, user browser localStorage access, local inference, deployment, live-site route change, model training or shared-resource lock mutation is part of UM-112.

## Reproduction and remaining gates

- Initial failing-first Node import: `ERR_MODULE_NOT_FOUND` before implementation.
- Focused isolated test: `node --test tests/mastery-receipts.test.mjs` — **11/11 passed** on Node.js 22 in the implementation workspace; committed module and test Git blob SHAs must be verified before claiming these are the exact tested bytes.
- Full combined repository suite: `npm test` on this PR exact HEAD; **pending GitHub Actions** until observed.
- Future separately owned work: trust-pinned sanitized receipt acquisition, size-limited ingestion, independent source/holdout rights review, responsive read-only UI with empty/error/stale states, and mobile/browser performance qualification. No speculative real-model numbers or auto-promotion.

**Owned paths:** `mastery-receipts.mjs`, `tests/mastery-receipts.test.mjs`, `docs/MASTERY_RECEIPTS.md`. All other PR lane files, external local queues and live three-route website remain unchanged.
