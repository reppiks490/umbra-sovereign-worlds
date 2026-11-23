# UMBRA Ω — 5,000 advanced synthetic experiment workflows (U0301–U5300)

**Status:** source for review; qualification depends on GitHub Actions results at the exact commit SHA. This implementation remains a fictional, deterministic civilization simulator. It does **not** establish verified real-world science, policy effectiveness, independent ML agent learning, trading profitability, artificial consciousness, or production deployment.

## Scope and intention

This catalog adds **5,000 individually addressable, manually dispatched GitHub Actions workflow files** alongside the existing 300 plus the original verification workflow. Each ID has a distinct tuple of experimental method, measured simulation observable, and controlled protocol. They are not 5,000 separate language models or separate source-code execution engines. Each invokes a **single audited shared simulation lab**: `scripts/umbra_advanced_lab.mjs`.

| Tier | IDs | Scope | Count | Methods |
| --- | --- | --- | ---: | --- |
| T4: Synthetic causal inference | U0301–U1300 | Controlled paired scenarios, dose-response, local curvature, interacting interventions, null-placebo falsification | 1,000 | 5 |
| T5: Adversarial resilience | U1301–U2300 | Policy-shock trajectories, downside tail risk, adverse-seed search, seed stability, multi-horizon drift | 1,000 | 5 |
| T6: Evolutionary search | U2301–U3300 | Bounded offline policy tournaments, held-out seed transfer, two-generation mutation, Pareto comparison, regime transitions | 1,000 | 5 |
| T7: Sovereign optimization | U3301–U4300 | Minimax regret, preference sensitivity, intervention budgets, regional dispersion, weighted multiobjective trade-offs | 1,000 | 5 |
| T8: Metascience and independent gates | U4301–U5300 | Exact replay, chunk equivalence, numerical/accounting fuzz, robust dominance, deliberately corrupted census detection | 1,000 | 5 |

**Design:** 25 executable analysis algorithms × 10 simulated observables × 20 variants = 5,000 uniquely configured experiments. Each method–observable tuple has twenty distinct seed, horizon, policy-axis, second-axis, intervention-size and stress-band variations. Observables are population, food, water, energy, wealth, knowledge, infected count, carbon, biodiversity and inequality. This is reproducible **within-model** research, not external causal inference.

## Reproducibility and evidence

The index `scripts/umbra_advanced_registry.json` references twenty deterministic `scripts/advanced_registry/shard_00.json` … `shard_19.json` files of 250 records each. This prevents a multi-megabyte monolithic registry from hampering code review. `scripts/generate_advanced_5000.py` recreates all 5,000 definitions from the recorded design; running it is optional and **does not dispatch Actions**.

Each individual manual workflow checks out repository source, invokes exactly one immutable-by-ID case, computes bounded synthetic statistics, validates current civic-accounting invariants, and writes an evidence file such as `advanced-evidence/U0301.json`. The output records the method, seed, policy, metric, engine version, method-specific results and a SHA-256 **checksum**. A checksum is an integrity checksum, **not a cryptographic signature, external source attestation, or scientific proof**.

- Only `workflow_dispatch` triggers exist on the 5,000 cases; never `schedule`, `push`, or pull-request side effects.
- `contents: read`; no GitHub secrets, network fetch in runner code, external model APIs, broker actions, pull-request merge, source modification or deployment.
- Each case has bounded simulation horizons, no more than a handful of synthetic policy candidates and finite seed ensembles; 12-minute individual Action timeout.
- Evidence artifacts expire after 7 days to manage storage; the source registry remains preserved in Git.
- The shared explicit CI runs 10 *shards* of 500 cases, not 5,000 simultaneously scheduled jobs.
- `scripts/validate_umbra_advanced_workflows.py` statically verifies all IDs, unique experimental combinations, safe trigger/permission contracts and evidence paths.

### Manual run (GitHub Actions screen)

Select a case `U0301` … `U5300` and tap **Run workflow**. GitHub's large workflow navigation may be slow or paginated; finding an ID through repository search is more reliable. Alternatively choose **UMBRA advanced experiments — manually execute one of ten 500-case shards**, select 0–9, and fetch the aggregated evidence artifact.

### Locally on an environment with the UMBRA engine

```bash
python3 scripts/validate_umbra_advanced_workflows.py
node --check scripts/umbra_advanced_lab.mjs
node scripts/umbra_advanced_lab.mjs --validate
node scripts/umbra_advanced_lab.mjs --id U0301 --out-dir advanced-evidence
node scripts/umbra_advanced_lab.mjs --audit-shard 0/10 --summary-file advanced-audit/shard-0.json
```

The full 5,000-case evidence audit is partitioned across 10 GitHub Actions jobs. When all ten complete successfully, **the simulator passed its synthetic stress suites**. Real scientific model validation, outside-data calibration and distributional validity remain blocked unless separately proven.

## Governance and failure response

All experiments run *read-only* against the **current repository simulation engine**. The source never writes back policies, mutates `main`, trains neural model weights, deploys code, or promotes a successful synthetic candidate. All source changes must follow `AGENTS.md` and the original `docs/ROADMAP.md` / `docs/MODEL_CARD.md` limitations. A fail in one of the 5,000 cases invalidates the overall aggregate claim; rerun the failed shard after an appropriately reviewed change. GitHub CI is the authoritative evidence for **real engine** compatibility; test-only fixtures are not.

The 5,000 new workflows belong solely to UMBRA workflow infrastructure. They are **not** the gated MYRIAD Ω→UMBRA or ICARUS OMNIGENESIS integration.
