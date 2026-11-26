# Authentic lesson retrieval and neural routing

Research-only paired development runs. No test partition inference, synthetic training or automatic promotion.

- lesson_retrieval.py: deterministic BM25 over 6,758 publisher-verified human-authored GSM8K training examples, excluding exact and number-normalized near duplicates. Qwen3 0.6B, two paired validation cases (offset 60): fixed 1/2, retrieved 2/2, four completed calls, one win and no losses. Exploratory only; pretraining and semantic overlap unknown.
- neural_routing.py: actual native NumPy MiniLM-L6 and BGE-small embeddings plus offline verified MS MARCO MiniLM-L6 cross-encoder, comparing mean cosine, cross-encoder and reciprocal-rank fusion. Live ICARUS query returned an exact verified quote from pinned main README using Qwen3 0.6B. Ranking changed; relevance and downstream superiority not established. Research route selection requires independent comparative evidence; not connected to production.
- 164 Python regressions passed; preceding Node run 193 passed; both CI workflows succeeded at 85d1256.
- Commands: python scripts/lesson_retrieval.py --root DATA_ROOT --count 2 --offset 60; python scripts/neural_routing.py --root DATA_ROOT --query "ICARUS causal market replay event clock and execution verification".
- Keep raw receipts local. Expand the paired protocol before promotion, test retention and additional model families, and use measured outcomes rather than candidate counts.
