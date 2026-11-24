# MYRIAD Ω × UMBRA — v3.0 cross-task admission tribunal

**Research-only.** This code is placed on UMBRA draft PR #21; no main branch merge, ICARUS PR #503 mutation, live broker authority, paid third-party model calls, automatic model promotion or scheduled Codex.

## Rationale

The original v2.5 PyTorch gradient candidates improved the same mathematical teacher family in v2.5/v2.7. The separate v2.8 preregistered target-family tribunal found **0 wins over the zero-output baseline out of 66 comparisons** across 10 real FP16 neural agent networks and the 10,000-adapter bank, with two independent fixed target seeds. v3.0 prevents future promotion of candidates when that kind of falsifying evidence is ignored or cherry-picked.

## Actual safeguards

- **Two fixed private v2.8 receipts required:** seeds `980004` and `980005`. No omitted, duplicate or extraneous seeds.
- Both must refer to the **same original archive and v2.5 candidate training receipt**. Original weights remain `imported_unverified`; no fabricated historic training attestation is accepted.
- Exactly **33 detailed comparisons per seed**, spanning three preregistered target families and the exact 10 agent identities + complete ability bank. Family summaries are recomputed from all per-subject MSE and flag fields, not trusted as supplied.
- Each row must beat *both* the original checkpoint and the zero predictor to count as a meaningful transfer win. Requires at least **6 of 11 wins in each family for each of two seeds** for `RESEARCH_REVIEW_ELIGIBLE`. This is an initial conservative research-screening heuristic, **not** a statistical validation or guarantee of real-world generality.
- For the **authoritative `audit` command only**, v3.0 invokes the existing v2.8 independent PyTorch FP16 replay of each original private receipt, checks all 33 results per seed and refuses changed/missing source or candidate weights. The cheaper in-memory `assess` function is for structural testing, not full model validation.
- Writes a brand-new private receipt with SHA-256 integrity, immutable destination, detailed per-family counts and explicit `production_authority=false`, `automatic_promotion=false`, `production_release_gates_verified=0`.
- A SHA-256 digest is **not an external identity attestation**; model training provenance and all 13 production release gates remain separate requirements. No current criteria can trigger a production merge or model promotion.

## Verified observed result

Run against the exact preserved v2.5 private FP16 candidates and v2.8 private receipts. Each of the two receipt files was independently re-executed from saved neural weights, including input and target reconstruction.

| Synthetic target family | Seed 980004 wins vs both baselines | Seed 980005 wins vs both baselines | Minimum required per seed |
|---|---:|---:|---:|
| Antipodal | 0/11 | 0/11 | 6/11 |
| Nonlinear interaction | 0/11 | 0/11 | 6/11 |
| Independent linear | 0/11 | 0/11 | 6/11 |

**Final result: `BLOCKED_TRANSFER_EVIDENCE`**, with 66/66 independent replay coverage. This explicitly falsifies any claim that v2.5/v2.7 neural candidates had already demonstrated meaningful *independent-task* transfer in these synthetic families. It does **not** disprove the observed original-task improvement or prove that all alternative model architectures will fail.

## Exact private re-execution

```bash
python3 scripts/evolution_cross_task_gate_v30.py audit \
  --archive /private/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip \
  --candidates /private/synthetic-v25-candidates \
  --receipt /private/v28-980004.json \
  --receipt /private/v28-980005.json \
  --out /private/v30-admission.json --authorize
python3 scripts/evolution_cross_task_gate_v30.py verify \
  --receipt /private/v30-admission.json
```

`verify` checks a research self-hash and policy flags; **only `audit`** replays the private neural FP16 files. Never represent a self-sealed report as external proof.

## CI, resources and next steps

The published CI performs only standard-library verification against deterministic fake receipts, **never touches private neural checkpoints**, and neither executes paid APIs nor starts scheduled tasks:

```bash
python3 -m unittest discover -s tests -p 'test_evolution_transfer_gate_v30.py' -v
```

**Next engineering priorities:** a task-conditioned model with train-only task-family exposure and a genuinely unseen family at evaluation, multiple null/random/constant baselines, hard run budgets, and independent dataset/license provenance. Have an external reviewer inspect the admission heuristic; 6/11 is not statistically guaranteed. Keep MYRIAD 13/13 owner release gates and ICARUS integration on hold.
