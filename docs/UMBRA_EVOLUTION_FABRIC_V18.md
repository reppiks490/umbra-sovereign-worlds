# MYRIAD Ω × UMBRA — Sovereign Evolution Fabric v1.8 (research-only, isolated)

**Snapshot: November 23, 2026.** This is review-branch research source, not a production release, 195,000 always-running LLMs, 250,000 independent sourced implementations, or a claim of real trading edge. MYRIAD's 13-gate release lock remains in effect. Do not merge to ICARUS / OMNIGENESIS until independently certified and owner-approved.

## Implemented source

| Component | Mechanism | Verified scope |
|---|---|---|
| Algorithm space | `scripts/umbra_evolution_mesh.py` | Exact 250,000 *parameterized algorithm configurations*; 25 executable optimizer–exploration combinations, NOT 250k independently invented algorithms |
| Sourced algorithm inventory | `scripts/evolution_source_registry.py` | 101 metadata references across 13 source directories including GitHub, TradingView, and Reddit. **No third-party executable code copied**, no license assumption, no quality certification. New candidates are metadata-only quarantine. |
| Workflow identity pool | `scripts/evolution_scheduler.py` | 195,000 independently addressable, persistent SQLite identities with spread hourly due times, leases, receipt hashes, run deduplication, review-only proposals, typed cross-worker peer read and crash recovery path. **Not 195,000 independent OS/LLM workers.** |
| Evaluation pipeline | `scripts/umbra_evolution_bridge.mjs` | Four read-only replay evaluations against actual UMBRA v5 synthetic engine on test runs, gated by civic invariants and receipt digest. No live broker, securities/data feed or production write authority. |
| Historical neural source | `scripts/myriad_bank_fabric.py` | Reads and verifies preserved 10 × 411k-parameter networks + 10,000 × 32-parameter adapter archive; checks SHA-256 overall and per row/batch. Complete historical 8.22 GB / 640 MB files and training ledgers are **not in portable project files**. |
| Newly trained candidate weights | `scripts/myriad_bank_fabric.py train-sample` | Ten real autograd PyTorch gradient-trained **candidates**, three steps each, 411k parameters each, all held-out synthetic losses improved after FP16 quantization; source checkpoint unchanged; candidates quarantined, private to ChatGPT Library and local workspace. |
| Bank expansion | `scripts/myriad_bank_fabric.py plan/provision` | Source-preserving immutable lineage with target 30GB agent and 10GB ability banks, and optional 64GB replay, 16GB causal evidence, 8GB retrieval capacity. **No expansion is marked trained** until full historical source hash/ledger checks and actual gradient training. Sparse reservation is NOT model training. |
| Website | `scripts/evolution_api.py`, `evolution/{index.html,style.css,app.js}` | Functional local 60fps animated constellation and five-brain board, live read-only SQLite evidence counters, worker inspection, algorithm/source/bank APIs, no write endpoints, localhost default. Diagram animation is **not agent compute**. |
| CI | `.github/workflows/umbra-evolution-mesh-ci.yml` | Validates full 250k/195k address spaces, security/determinism tests and real UMBRA engine replay after merged branch code checkout. Test outputs will become confirmed only when GitHub Actions has actually run on this exact commit. |

## Source lineage and expanded bank exact geometry

- Historic originals: `10,000 × 411,000 × 2 = 8,220,000,000` FP16 bytes, and `10,000,000 × 32 × 2 = 640,000,000` FP16 bytes.
- Expanded targets: `10,000 × 1,500,000 × 2 = 30,000,000,000` bytes; and `10,000,000 × 500 × 2 = 10,000,000,000` bytes.
- Non-destructive additional storage: **21.78 GB** per-agent layer and **9.36 GB** per-ability layer. No automatic baseline replacement.
- Additional aspirational bank capacities: 64GB experiment replay, 16GB causal evidence, 8GB retrieval memory. Total **128GB capacity plan** inclusive of 30+10 agent/ability banks. Not all allocated or trained.
- Preserved subset archive: `MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip` (private user Library, `/MYRIAD-OMEGA/v1.6/`). The archive's SHA256 is stored in local training report. This is a **ten-agent subset**, not the full bank. The original 8.22GB/640MB bank on a previous execution host was **not retrieved or independently imported** in this session.
- The only procedure to expand the full original bank is `provision --agent-dir ORIGINAL --ability-dir ORIGINAL --out NEW --approve`, which refuses missing source files and ledgers. The preflight now SHA-256 verifies all 10,000 original agent rows and every historic ability batch, including status and steps, before provisioning any expansion.

## Validation and usage

```bash
python3 scripts/umbra_evolution_mesh.py validate --full
python3 -m unittest discover -s tests -p 'test_*evolution*.py' -v
python3 scripts/evolution_source_registry.py validate
python3 scripts/myriad_bank_fabric.py plan
# Archive optional; do not ship historic checkpoints into public GitHub:
python3 scripts/myriad_bank_fabric.py inspect-sample --archive ~/private/MYRIAD_COUPLED_10_AGENT_10000_ADAPTERS.zip
python3 scripts/evolution_scheduler.py --db ~/private/mesh.sqlite3 init
python3 scripts/evolution_scheduler.py --db ~/private/mesh.sqlite3 run --max-jobs 128 --steps 12
python3 scripts/evolution_api.py --ledger ~/private/mesh.sqlite3 --port 8797
# Open http://127.0.0.1:8797/ on same machine
```

The scheduler stores every worker's next due time, completion count, lease owner, receipt and quarantined candidate. Concurrent hosts require a shared database and higher-volume message infrastructure rather than using separate ephemeral GitHub runner SQLite files. 195,000/hour is a capacity objective, not a certified SLA. Gated hourly GitHub Actions are a smoke/stability demonstrator, not a substitute for an always-on distributed control plane.

## Safety and economic controls

1. Keep model and training weights in private storage, never commit them into a public repository.
2. Require source URL, hash, upstream license, and independent security evaluation for third-party algorithm code. Reddit ideas require independent verification and do not establish financial edge.
3. Require chronology-correct market datasets, realistic slippage/fees, purged temporal folds, registered hypotheses and post-selection correction before any trading claim.
4. Recompute hash-qualified peer receipts, do not accept self-reported scores as truth, and do not auto-promote model parameters.
5. Any future external model connector must have auth scopes, request quotas, cost ceilings and a human approval gate before production-side effects.
6. The website is read-only and binds to localhost by default. For iPhone, use an authenticated HTTPS reverse proxy, never expose the local bare server or credentials publicly.
7. The previous user requirement prohibited Codex in all scheduled tasks. No Codex is used in this subsystem.
8. No UMBRA main-branch, ICARUS PR #503, or live brokerage integration is authorized until MYRIAD's 13/13 release gates pass and explicit owner approval is recorded.

## Required follow-up engineering

- Recover the historic original full banks and ledgers from the prior host or securely create **new** weight versions with labeled lineage; do not mislabel new random values as original trained weights.
- Prove genuinely independent algorithm acquisitions at increasing validated counts, not merely variations. Metadata seed inventory is 101 names/ideas from real source directories and has zero copied third-party implementations.
- Replace single-machine SQLite with centrally authenticated high-availability Postgres, queue leases, immutable object store and worker/service metrics. Profile and certify 195k hourly learning tasks on chosen hardware before enabling full cadence.
- Upgrade synthetic policy training to real model-backed learning and independent benchmarks for general intelligence, coding, trading and practical tasks; independently review trading evidence before any broker permission.
- Separate change proposals, CI review, rollback and explicit promotion; one new idea per workflow run is a *candidate*, not automatically a proven new feature or integration.
- If deploying the website, stage an isolated service with read-only endpoints and HTTPS/authentication; do not modify an existing public UMBRA application in place without a review.