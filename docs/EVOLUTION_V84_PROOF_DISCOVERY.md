# v8.4 — proof-carrying length generalization and discovery queue

## Live result, before the new experiment

The installed v8.2 local model completed seed 124690: 4 attempted, 4 completed, 1 correct answer, 0 correct witnesses, 0 jointly correct, no reported execution errors. Observed sanitized aggregate at 2026-11-24T19:03:41Z, PC process 26592. The one-shot phase request was consumed and claim count 1. This is an actual model evaluation, not fixture scores. The runtime verified its saved receipt before aggregate publication; independent private receipt re-audit remains open. Negative outcome is retained. No promotion.

v8.3 commit dceb0d1b8dab2d4bceb69550e62c4d3b07321f67 passed 24/24 CI workflows; local experiment 6/6 tests. It remains an isolated candidate, not a live training policy. Its loss against group-balanced training on 9/12 seeds remains the key intervention constraint.

## External research and skill discovery

- CLRS-Text README independently retrieved through GitHub: https://github.com/google-deepmind/clrs/blob/master/clrs/_src/clrs_text/README.md, observed blob 2262dabbff2fb5314f65bd2b68467902ac069207. Explains thirty algorithms and length extrapolation; source repository LICENSE observed blob d645695673349e3947e8e5ae42332d0ac3164cd7 (Apache-2.0). No external source or dataset copied. Dataset-specific licensing and splits must still be checked before ingestion.
- omgskills read pinned, hash-verified scientific brainstorming and critical thinking skill excerpts from k-dense-ai/scientific-agent-skills at 5f2bc0341354fd5590aef76a533ada1e1e5b4e62. Use independent hypotheses, disconfirming evidence, predeclared criteria, raw negative results, and separate ideation from validation. Read-only; no external skill installed, no instructions or scripts executed.
- New capability inspired by the benchmark and failed witnesses: proof-carrying reasoning instead of exact matching a single witness. Each generated instance accepts any valid optimality certificate.

## Implementation and exact qualification

Two directed graph families: shortest path (feasible route and dual potential inequalities) and max flow (capacity feasibility, conservation, and matching cut). Independent deterministic solver and verifier. Bounded integer input, unique edges, bounded vertex count, antiparallel edges supported. No model inference yet. Sizes 4/8/16/32, 12 seeds per family and size, original and label-permuted/scaled variants: 192 verified certificates, 48 each size. Small cases independently checked with exhaustive paths/cuts; invalid types and tampered certificates rejected. RED missing module; GREEN 5/5 tests; independent qualification 192/192. Exact tested local blobs 5aa81c119b8556b884de007a7b5e97e847d4cf8a and ee46468af7dd3f577c94c18ec777ebf798e7e242. New CI pending. Do not count two new graph tasks as trained abilities or model successes. No new algorithm counter claim (existing algorithms overlap; novelty is verifiable certificate and curriculum harness).

## Discovery tracks: proposals, not installed systems

1. **Proof-assisted reasoning**: evaluate direct model, typed tool selection, and verifier-mediated correction against same fresh tasks, fixed call/token budget and independent evaluator. Report direct and assisted separately; tool-computed answer is not autonomous reasoning.
2. **Robust neural training**: extend v80 with matched-budget balanced and adaptive group loss on fresh distribution families; compare per-agent worst-group outcomes, retain losses; blocked by local training admission until eligible.
3. **Point-in-time causal data**: FactorWeave manifest identifies historical factor and regime features. First confirm license and as-of availability, then build temporal split/embargo and synthetic leakage tests. Keep provider data private, no live trading.
4. **External reasoning datasets**: CLRS-Text and WILDS discovery; validate exact dataset revision/license, leakage and scale before using, no benchmark contamination or paid acquisition.
5. **Observatory evidence UX**: separate logical catalog, inference identities, authenticated checkpoints, failed cases, research/production gates and freshness. Explore visual/interface research connectors without production deployment; use truthful evidence views, not fabricated telemetry.
6. **Discovery ledger**: record each proposal's provenance, assumption, counterexample, resource class, measurable success criteria, independent controls and actual outcome. No auto-promotion or arbitrary execution of external content. Discover new directions without merely making tool calls for their own sake.

Prioritize eligible actual training/inference and independent evidence over new version labels. Preserve all 13 release gates, existing schedulers, no Codex/paid resources/private artifact export, draft PR #21 only.
