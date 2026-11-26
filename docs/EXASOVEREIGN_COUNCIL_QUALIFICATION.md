# Collective intelligence qualification: development evidence (2026-11-25)

This research-only subsystem measures a fixed three-model panel using pinned original GSM8K development validation records, with one human-written training example per prompt. It does not update weights or authorize production use.

- scripts/council_qualification.py: strict majority, weight identity, matched cases, abstentions, baseline attribution and inference cost.
- scripts/council_ledger.py: nonoverlapping validation windows, immutable-by-convention content-addressed receipts, paired counts and exploratory sign tests.
- scripts/council_receipt_audit.py: replays receipt scoring against digest-verified original labels; no fresh inference.
- Run with the existing native Python environment: python scripts/council_qualification.py --root DATA_ROOT --count 2
- Audit: python scripts/council_receipt_audit.py --root DATA_ROOT

Observed local trials: offsets 40 and 0; four unique development cases; twelve completed model calls (Granite 350M, Qwen3 0.6B, Gemma3 1B), 143.985 seconds aggregate. Each model and the ensemble scored 1/4. Ensemble answered one case, correctly, and abstained on three. No paired wins or losses. Both receipts replayed successfully. This is a negative accuracy result, not evidence of generalized reasoning or improvement. Public benchmark pretraining contamination remains unknown. No synthetic training, final test inference, or promotion. Local regression: 156 Python and 193 Node tests; Node suite preceded final Python-only ledger/audit additions.

Next research: compare source-retrieved authentic worked examples against fixed examples on matched development cases, strengthen independent relevance evaluation and specialist execution, assess transfer and retention before any weight promotion. Keep raw trial records local; do not commit model weights or corpus data.
