# MYRIAD Ω × UMBRA — v2.6 durable model-backed research queue

**State:** research-only, default OFF. No independent language-model workers are started by this commit. UMBRA/ICARUS production branches are untouched. MYRIAD's 13/13 independent release gates and explicit owner approval remain mandatory.

## Purpose and actual implementation

The existing 195,000 independently addressable logical workflow identities have only been exercised by synthetic optimization runs. This phase introduces a **separate SQLite WAL durable queue** that can bind a **small, explicitly enrolled subset** of those identities to the v2.4 private model-evaluation adapter when a verified local model endpoint is supplied.

- All `E000001`–`E195000` worker IDs are addressable; **none are auto-enrolled** and no models are automatically launched.
- Explicitly enroll **at most 128 IDs per call**, optionally recurring every 3,600 seconds; no default hourly schedule or full-fleet registration. Each actual `run` is independently authorized and bounded to **four workers**, **four toy evaluation prompts per worker**, per-call token caps and an elapsed-time checkpoint.
- Lease claims use SQLite `BEGIN IMMEDIATE`, unique worker IDs and a random invocation-specific owner token. Expired/reclaimed leases cannot be completed by their former owner. **Completion checks the current wall clock after model inference, not the earlier claim timestamp; results arriving after the lease deadline fail closed.** Separate `model_runs` primary keys provide idempotent per-hour receipts.
- Each completion requires a **private regular JSON file** with a v2.4 HMAC, independently replayed arithmetic scoring, `production_authority=false`, the deterministic seed derived from the exact `(worker_id, scheduled_hour)`, and a filename scoped to the same occurrence.
- Failed evaluations enter a **quarantined** state, not an automatic-retry-and-promote state. The separate private raw output is never written into the SQLite database or public repository. Only the HMAC digest, local evidence path, completed requests, score, and previous-hour digest are stored.
- The `previous_hmac` chain is **an archival lineage link**, not evidence that one model learned from another. No model checkpoint or optimizer is automatically updated, no code is automatically integrated or merged, and no broker orders are possible.

### Reproduction: no model execution

```sh
python3 scripts/evolution_model_queue_v26.py status --db PRIVATE_MODEL_RESEARCH.sqlite3
python3 scripts/evolution_model_queue_v26.py enroll --db PRIVATE_MODEL_RESEARCH.sqlite3 --start 1 --count 4 --due-hour 2026-11-24T03 --repeat-hourly
python3 scripts/evolution_model_queue_v26.py status --db PRIVATE_MODEL_RESEARCH.sqlite3
```

The `enroll` command explicitly stores a future scheduling intent but **does not itself start a daemon, GitHub Action, ChatGPT automation, model server, or background job**. Hourly execution requires an operator-run/supervised hosting process and validated resource budget.

### Explicit opt-in: one bounded local inference batch

Configure `MYRIAD_LOCAL_MODEL_TOKEN` and a separate private `MYRIAD_EVIDENCE_HMAC_KEY` through an authorized local secret-management mechanism. Do not commit or paste secrets into logs. With an accessible OpenAI-compatible model running on numeric IPv4 loopback:

```sh
python3 scripts/evolution_model_queue_v26.py run --db PRIVATE_MODEL_RESEARCH.sqlite3 --private-out PRIVATE_RECEIPTS_DIRECTORY --port 11434 --model YOUR_PINNED_LOCAL_MODEL --max-jobs 2 --count 2 --max-tokens 16 --budget 32 --timeout 10 --deadline-seconds 30 --authorize-local-model
```

The upstream server's model identity and token usage are **self-reported**. This is an explicit research command; no permanent model-backed fleet has been demonstrated. The v2.6 CI runs deterministic fixture-backed tests with **zero external model or paid API calls**.

## Failure and provenance tests

- Reject ID zero, ID beyond 195,000, duplicate enrollment and batches exceeding 128 identities.
- Simultaneous owners lease distinct workers; earlier owners cannot complete a stolen or expired lease. A separate regression simulates a late model response after a 120-second lease and verifies that the result is never accepted.
- Signed private evidence must pass v2.4 output replay and HMAC verification; valid receipts bound to the **wrong worker/seed or wrong scoped filename** are rejected even when internally HMAC-valid.
- Two mocked local model evaluations generate two independently verified occurrences; the recurrence advances to the next hour instead of running again before due.
- Failed model execution is quarantined and cannot automatically re-enter processing; absent user authorization and excessive budgets make no claims and no inference calls.
- Public CI verifies **source, scheduling, and mock-evaluation behavior only**. It cannot certify real LLM inference, training, a hosted server, a 195,000-per-hour SLA, operational cost or trading performance.

## Other project evidence preserved

v2.3 portable checkpoint evidence gate, v2.4 private model evaluator, v2.5 actual PyTorch training of ten agent candidates and 10,000 ability candidates, and the 390,000 synthetic-history archive are separate evidence streams. The ten-agent source sample still says `imported_unverified`. Original full 8.22 GB/640 MB historical banks and ledgers have not been recovered, and 30 GB/10 GB training bank targets are not complete. The historic 389,987 asserted peer uses lack parent source hashes and are not independently proven; v2.1 only fixes that for future records.

**Next gate:** independently run a pinned, authorized real local model (not a fixture), then verify full private output provenance and score against a genuinely held-out, license-qualified benchmark before enrolling larger worker groups. No Codex for scheduled tasks. No UMBRA or ICARUS main merge without 13/13 MYRIAD gates and explicit approval.

**Knowledge delta:** `scripts/evolution_model_queue_v26.py`, `tests/test_evolution_model_queue_v26.py`, `docs/EVOLUTION_V26_DURABLE_MODEL_QUEUE.md`, `.github/workflows/myriad-model-queue-v26-ci.yml`, `research/EVOLUTION_V26_SOURCE_MANIFEST.json`.
