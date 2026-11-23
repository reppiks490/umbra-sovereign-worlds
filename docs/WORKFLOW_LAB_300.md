# UMBRA Ω — 300 additional, manually invoked GitHub Actions workflows

**Status:** Workflow source and lab runner implemented for review. GitHub Actions remote run results must be separately checked at the exact target commit. This is a *fictional deterministic civilization simulation*, not a validated climate/economic/political predictor, LLM trainer or autonomous trading engine.

## Purpose

The UMBRA repository previously had one existing Actions entry: **UMBRA Sovereign Worlds verification** (`.github/workflows/unit.yml`). This package adds **300 distinct Actions workflows** in `.github/workflows/`:

| Range | Level | Workflows | Action |
| --- | --- | ---: | --- |
| U001–U100 | I — verification | 100 | Reproducibility, bounded stocks, ledger/faction/corridor invariants, passport rejection, null controls, court checks. |
| U101–U200 | II — experiment/research | 100 | Paired synthetic interventions, seven-axis sensitivity designs, seeded comparisons, uncertainty reports and simulation outcomes. |
| U201–U300 | III — bounded simulation evolution | 100 | Contender-policy tournaments, multiobjective comparisons, transfer across seeded worlds, worst-seed robustness and no-promotion evidence. |

Each 100-workflow tier covers **20 distinct families × 5 increasingly demanding scenario profiles** (`baseline`, `edge`, `stress`, `cross-seed`, `adversarial`). A workflow ID has its own purpose, inputs, deterministic output hash and downloadable JSON evidence. They are *not* 300 independent AI services, 300 trained agents, 300 different runtime architectures or 300 deployers.

## Execution and safety

- **All 300 new workflows use `workflow_dispatch` only.** They do not schedule themselves, start on every push, access secrets, deploy a website, touch real finances, trigger broker orders, merge code or create automated agents. No Codex used.
- Each workflow has `permissions: contents: read`, an 8-minute timeout and cancel-in-progress concurrency within its own workflow/ref.
- Each uses Node 22, `scripts/umbra_lab.mjs`, the existing v5 engine/society/Reality Court and uploads exactly one named JSON artifact retained for 14 days.
- Evidence explicitly declares `syntheticOnly`, false scientific validation and false production permissions; all selected policy candidates remain **offline comparisons only**.
- The existing `unit.yml` remains auto-CI on `main` and PRs. Its original Node and browser tests remain intact. The new catalog validation and aggregate 300-case synthetic suite run once per CI job **rather than causing 300 automatic jobs**.
- There are no secrets or new paid external providers. Each manual run consumes GitHub-hosted runner resources under the repository's account and plan limits.

## Commands

From the repository root on Python 3.10+ / Node 22 (no npm dependency install needed):

```bash
python3 scripts/validate_umbra_workflows.py
node --check scripts/umbra_lab.mjs
node scripts/umbra_lab.mjs --validate
node scripts/umbra_lab.mjs --id U001 --out-dir workflow-artifacts
node scripts/umbra_lab.mjs --id U105 --out-dir workflow-artifacts
node scripts/umbra_lab.mjs --id U220 --out-dir workflow-artifacts
node scripts/umbra_lab.mjs --audit-all
npm test
```

Individual workflow artifact `workflow-artifacts/Uxxx.json` contains `caseId`, engine version, synthetic outcomes, local assertions and deterministic SHA-256 digest. The runner is pure local evaluation; no automated model updates occur. Never merge a winner into live models or infer real-world interventions from UMBRA's fictional results.

## GitHub Actions visibility

GitHub's **Run workflow** control for `workflow_dispatch` workflows requires those YAML files to exist on the repository's **default branch**. Therefore, a staged feature branch or PR by itself will **not** place the 300 entries in the iPhone Workflows menu. After remote CI and independent review, land the verified workflow definitions on `main`. A workflow can be listed without any run history; first manual run creates that history. The mobile app may paginate/collapse the list.

## Acceptance and incident gates

1. Validate exactly 300 new YAML files with unique IDs/names, manual-only triggers, read-only permissions and finite timeout.
2. Run `npm test` and the 300-case aggregate suite against the real source engine; fix failed experiments rather than modifying tests to claim success.
3. Keep model-scope language synthetic; Reality Court real-world validation rows remain blocked.
4. Verify the original existing browser viewport tests and GitHub Actions remote workflow status on the exact PR SHA.
5. Check that landing these files on `main` adds exactly 300 new workflow definitions, not 300 automatic jobs. Confirm one manual run and downloadable evidence if desired.
6. Do not add an autonomous schedule, secret-bearing API call, real trading integration or MYRIAD component to UMBRA. The MYRIAD→UMBRA/OMNIGENESIS integration gate remains separate and CLOSED.

## Source files

- `.github/workflows/umbra-u*.yml` — 300 manual workflow definitions.
- `scripts/umbra_workflow_registry.json` — canonical 300-case catalog and experiment inputs.
- `scripts/umbra_lab.mjs` — reproducible local case runner + aggregate suite.
- `scripts/generate_umbra_workflows.py` — deterministic generator for identical YAML definitions.
- `scripts/validate_umbra_workflows.py` — standard-library-only independent structural validator.
- `.github/workflows/unit.yml` — existing workflow with aggregate catalog verification added.

**Engineering ≠ scientific validation.** A pass establishes only that the code fulfilled internal model constraints on synthetic data.
