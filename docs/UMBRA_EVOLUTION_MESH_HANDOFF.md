# UMBRA Ω — 250K Experiment Space × 195K Logical Evolution Mesh (v0.1)

**Research-only draft. NOT a full-scale deployment, not 250,000 new independent discoveries, and not 195,000 live GitHub Actions workflows.** No MYRIAD/ICARUS integration is authorized; their existing completion/release lock remains unchanged.

## Delivered implementation

- `scripts/umbra_evolution_mesh.py`: deterministic indexing for **250,000 unique parameterized experiment recipes** (`5 exploration operators × 5 optimizers × 100 simulation regimes × 100 objective settings`) and **195,000 distinct logical workflow identities** (`195 cohorts × 1,000`). Algorithm specifications are lazily generated, not 250,000 independently designed mathematical algorithms. 25 actual strategy combinations are implemented.
- Each bounded workflow run adjusts eight **toy policy parameters** using finite differences, SPSA, coordinate updates, random direction or mirrored perturbations, paired with SGD, momentum, RMSProp, Adam or trust-region updates. It trains across four synthetic folds, checks two held-out folds and two synthetic stress folds. These parameters are **not LLM weights** or MYRIAD's historic 411,000-parameter weights.
- SQLite WAL evidence ledger enforces unique `(hour, workflow)` receipts; receipts use deterministic SHA-256 canonical JSON; bounded peer assimilation reads a previous same-domain record only after a hash check. Shared evidence is local to the same persistent database. Distinct shards or hours on ephemeral GitHub-hosted runners **do not share memory** unless independently operated durable storage is supplied.
- Hourly ID rotation prevents permanent starvation. The scheduler reports `capacity_deferred`, the exact amount it did not run; it **cannot guarantee 195,000 evaluations each hour**.
- `scripts/umbra_evolution_bridge.mjs` evaluates bounded proposals against **actual UMBRA v5 synthetic `engine.mjs`** on paired seeds, checks `civicAudit`, and reports non-promoted metrics. This is a bridge from toy training to the repo's existing simulator, **not a real-world validation**.
- `tests/test_umbra_evolution_mesh.py` exercises all 25 operator combinations, full uniqueness enumeration, deterministic training, SQLite receipts, peer integrity, shard coverage, and negative input cases.

## Deployment and authority policy

- Everything is sandboxed, synthetic and non-trading; no code generation/editing or repository mutations occur in the runner; every proposal is quarantined for separate independent review.
- Proposed GitHub Actions hourly orchestration is **OFF BY DEFAULT** using the repository variable `UMBRA_EVOLUTION_ENABLED`. It becomes schedule-eligible only if reviewed and merged to the default branch, the user deliberately sets that variable, and runner/cost/CI qualification is complete.
- The default guarded hourly orchestration would only process **8 shards × 32 identities = up to 256 toy training tasks/hour**; this is deliberately not 195K/hour. A deployer must add durable cross-run storage and demonstrate capacity, memory, cost, backpressure and safety budgets before increasing workload.
- No scheduled Codex or autonomous GitHub writes. `contents: read` only. GitHub-hosted artifacts contain bounded research evidence and no secrets.
- **Full-coverage throughput requirement:** 195000/3600=54.17 fully evaluated identities/second, excluding 250,000-algorithm curricula and collaboration overhead. User laptop with 16GB RAM and standard GitHub Actions are NOT certified for this.

## Reproduce on checkout

```bash
# On the review branch with the archive unpacked into repository root:
python3 scripts/umbra_evolution_mesh.py validate --full
python3 -m unittest discover -s tests -p 'test_umbra_evolution_mesh.py' -v
python3 scripts/umbra_evolution_mesh.py tick --hour 2026-11-23T19 --shards 256 --shard 0 --limit 8 --steps 8 --ledger /tmp/umbra_mesh.sqlite3 --output /tmp/umbra_mesh.jsonl
node scripts/umbra_evolution_bridge.mjs --input /tmp/umbra_mesh.jsonl --output /tmp/umbra_bridge.json --limit 4
```

If using the source bundle stored at `research/evolution_mesh_v1.tar.gz`, first run:

```bash
tar -tzf research/evolution_mesh_v1.tar.gz   # inspect members first
tar -xzf research/evolution_mesh_v1.tar.gz
```

The versioned archive contains editable human-readable Python, JavaScript, tests, and this handoff. It was archived for transport into the connected GitHub repo; it is not an obfuscated executable. No archive content is executed by extraction alone. Confirm tar member paths before extraction.

## Acceptance gates for future expansion

1. Publish and verify current PR CI on GitHub against UMBRA's actual `main` source and check exact source SHA.
2. Independently qualify proposed algorithms on relevant authentic simulation tasks; do not call 250K parameter combinations 250K novel ideas.
3. Add persistent, authenticated, access-controlled, cross-hour, cross-shard event store and replay-recovery semantics.
4. Implement resource-efficient distributed scheduling with explicit hourly SLA/coverage, budget ceilings and backpressure.
5. Demonstrate model-backed generalization outside synthetic teacher fixtures; evaluate accepted vs rejected changes with statistical uncertainty.
6. Build a separately approved feature/patch pipeline with review, test, rollback and no direct model-to-main merges.
7. Retain MYRIAD's 13/13 completion lock before any cross-repo integration with OMNIGENESIS or UMBRA.

## Honesty manifest

`algorithm_specs=250000; implemented_strategy_combinations=25; logical_ids=195000; default_live_hourly_scheduled=0; original_full_MYRIAD_weight_banks_recovered=false; production_ai_integrations=0; automatic_feature_promotions=0; real-world_performance_verified=false.`
