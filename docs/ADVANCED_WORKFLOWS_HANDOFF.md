# UMBRA Ω — advanced workflow generation / takeover

User request: Add another 5,000 highly advanced workflows to the GitHub mobile Workflows screen in `reppiks490/umbra-sovereign-worlds`, preserving the previous 300 manual workflows and the original `unit.yml`.

- U0301–U5300 individually selectable GitHub Actions YAML, five tiers T4–T8, 25 algorithm families, ten metrics, twenty deterministic variants, 5,000 unique combinations.
- Code: `scripts/umbra_advanced_lab.mjs` (25 real synthetic algorithms), `scripts/generate_advanced_5000.py`, `scripts/validate_umbra_advanced_workflows.py`, `scripts/umbra_advanced_registry.json` + 20 shard files.
- CI: `.github/workflows/umbra-advanced-5000-ci.yml` validates static contracts and runs every case in 10 finite, independent batches. Manual `.github/workflows/umbra-advanced-5000-batch.yml` runs any 1/10 batches.
- No auto-run from 5,000 case definitions. Only newly introduced CI job automatically triggers on PRs and main path changes. Read-only, no secrets or side effects.
- Verification must read actual CI logs (aggregate ten shards, base Node tests and UI smoke), pinned to exact SHA. A test-only simulation fixture is used locally for protocol sanity; never claim it verifies the real engine.
- Release rules: preserve model semantics `AGENTS.md`, do not install MYRIAD as an integration, do not claim scientific truth or full intelligent agent training. Do not touch Icarus OMNIGENESIS.
- If workflow volume breaks GitHub UI or API, preserve the 5k registry and provide an alternative indexed batch-runner UX; do not falsify visibility claims.
