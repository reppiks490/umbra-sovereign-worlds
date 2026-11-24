# Evolution v2.2: bounded local model evaluation

Research-only continuation of draft PR #21. The previous v2.1 scheduler and
archived evidence are unchanged. This is a separate opt-in inference adapter,
not a fleet integration or a training claim.

## Acceptance and constraints

- Only numeric IPv4 loopback, fixed OpenAI-compatible chat-completions route,
  no redirect or proxy following, explicit authorization and local bearer token.
- At most eight requests, 64 requested completion tokens per request, and a
  preflight aggregate requested-completion budget. Provider-reported usage is
  checked, not independently measured; a noncompliant endpoint can exceed
  the requested cap. This is not a monetary budget or a hard wall-clock limit.
- Seeded arithmetic tasks and exact-match scoring are a toy capability check,
  not an independent general-intelligence or trading benchmark.
- Exclusive private receipt path, no automatic retries, no raw responses or
  bearer token persisted. A failed call stops the run and records incomplete
  status; a process crash can leave a partial file which verification rejects.
- Receipt hashes detect accidental modification; a re-sealed fabricated receipt
  is not proof of model identity or output. The checker validates task lineage,
  coverage and aggregates but cannot replay hash-only outputs.
- No external model calls in CI, no paid services, no live orders, no automatic
  promotions, no changes to ICARUS, no main merge. The test HTTP server is a
  deterministic fixture, not an actual neural model.

## Reproduction

Run the standard-library tests:

```sh
python3 -m unittest discover -s tests -p 'test_evolution_local_model_v22.py' -v
```

For an owner-authorized local OpenAI-compatible model endpoint, set
MYRIAD_LOCAL_MODEL_TOKEN privately and run:

```sh
python3 scripts/evolution_local_model_v22.py run --port 11434 --model YOUR_MODEL --seed 17 --count 4 --max-tokens 16 --budget 64 --out private-receipt.json --authorize
python3 scripts/evolution_local_model_v22.py verify private-receipt.json
```

The actual server must implement the exact response model identifier and
completion-token usage fields. No live inference has been claimed by this
source change. Next: independent held-out evaluation with private raw output
retention, pinned model artifact digest, hard total deadline, verified checkpoint
coverage, and a separate controlled scheduler integration. Keep release gates
closed pending evidence and owner approval.
