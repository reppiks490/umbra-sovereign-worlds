# UMBRA Ω synthetic daily fleet execution — v1 operations

The repository contains **5,300** manually dispatched numbered YAML workflows: `U001..U300` and `U0301..U5300`, plus 4 other default-branch workflows. Creating 10,600 independent GitHub Actions workflow runs every day (each numbered file twice) is not enabled. Instead, the **underlying scenario engine for every numbered workflow executes twice daily in read-only bounded batches**, then a coverage verifier checks all 5,300 results. The individual manual workflow YAMLs are unchanged and are **not independently triggered**. Do not describe batch case execution as 10,600 workflow runs.

Schedule on **GitHub's default branch only**: `03:23 UTC` and `15:23 UTC` each day. GitHub may delay queued scheduled events; the workflow records run success, but no hard timing guarantee. An environment variable `UMBRA_DAILY_FLEET_DISABLED=true` disables the catalog gate if cost or infrastructure conditions require. No backend service, deployment, trading, secrets, Codex or fee-bearing inference tasks are activated.

The catalog job validates all numbered workflow definitions and runs the deterministic registries; the base runner executes 300 synthetic cases; ten capped shards each execute 500 advanced cases, with two shards running concurrently; the final job verifies 11 receipts cover all 5,300 without failures. Source scripts and artifact SHA256 are checked by the existing CI. This does not test individual workflow scheduling semantics or scientific real-world generalization.

When scheduled jobs are disabled due to 60 days without repository activity or due to repository/organization policy, restore them through an owner-reviewed GitHub workflow-management action. Do not add autonomously recurring paid providers or broker activities.

For safe local TDD:

```sh
python3 -m unittest discover -s tests -p 'test_daily_fleet.py' -v
python3 scripts/validate_daily_fleet.py schedule
```
