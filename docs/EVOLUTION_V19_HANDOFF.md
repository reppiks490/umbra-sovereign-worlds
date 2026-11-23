# MYRIAD Ω × UMBRA — v1.9 current-session takeover

**Read the source code and tests instead of rebuilding from scratch.** Research-only GitHub branch `reppiks490/umbra-sovereign-worlds:agent/evolution-fabric-v18-research`, draft PR #21. Confirm current commit before any edits. Source work still isolated from Icarus OMNIGENESIS PR #503 and UMBRA `main`.

## New files
- `scripts/evolution_algorithms_v19.py` — 12 mathematically distinct bounded optimizers (no external dependencies), five synthetic objectives, deterministic seeded benchmarks and immutable result records.
- `scripts/evolution_tournament_v19.py` — emit bounded, SHA256-checkable v1.9 research candidates under the existing v1.8 receipt envelope for UMBRA's real `engine.mjs` bridge.
- `scripts/evolution_transfer_curriculum_v19.py` — correlated vs hard-shift transfer tests.
- `scripts/evolution_tribunal_v19.py` — independently replay all v1.8 research records, bounded row range checkpoints, hash-checked contiguous range aggregation, older independently verified cross-domain research linking.
- Three new test files, v1.9 source manifest and research aggregate receipt; updates to read-only API + frontend.

## Verified on local test host
- v1.9 benchmark: 12 methods × 5 tasks × 10 seeds × 3 budgets = 1,800 optimizer trials, plus 1,800 separate structural-transfer trials. Full raw reports stored privately in ChatGPT Library and hashed; no source training data are vendor market data.
- Distribution shift: 12/12 improve train medians at each budget, **0/12** improve unrelated shift medians; correlated synthetic holdout 12/12 positive (not a proof of wider mastery).
- Independent tribunal: all 195,000 **existing stored** synthetic research receipts replay and match, zero hash/identity/metric failures, 18,402 quarantined proposals.
- Version-specific tests run under `python -m unittest discover -s tests -p 'test_evolution_*v19.py' -v` (glob patterns may vary), and JS bridge under Node 22. Execute original UMBRA main CI on the exact review commit.

## Fresh clone commands
```sh
python3 -m unittest discover -s tests -p 'test_evolution_algorithms_v19.py' -v
python3 -m unittest discover -s tests -p 'test_evolution_transfer_v19.py' -v
python3 -m unittest discover -s tests -p 'test_evolution_tribunal_v19.py' -v
python3 scripts/evolution_algorithms_v19.py --budget 64 --seeds 3 --output /tmp/v19-algorithms.json
python3 scripts/evolution_tournament_v19.py --start 1 --count 12 --budget 48 --output /tmp/v19-candidates.jsonl
node scripts/umbra_evolution_bridge.mjs --input /tmp/v19-candidates.jsonl --output /tmp/v19-umbra-bridge.json --limit 12
python3 scripts/evolution_api.py --port 8797
```

## Compulsory release controls
- GitHub CI on current PR SHA. Neither 195K hourly model-generation throughput nor 250K independently invented algorithms are achieved.
- Full neural banks absent: original FP16 + SQLite ledgers from training host must be recovered privately; *do not substitute sparse allocations for trained data*.
- Keep default-branch hourly autonomous integration DISABLED and changes quarantined. No broker, no private API keys, no Codex scheduled tasks, no unreviewed model weight promotions or push to `main`.
- Railway project `MYRIAD Evolution Observatory` exists but first deploy failed for repo authorization. Require user authorization in Railway, then deploy exact reviewed branch. The iPhone URL is currently unverified.

Existing v1.8 recovery: `docs/EVOLUTION_FULL_FLEET_HANDOFF_20261123.md`, `docs/UMBRA_EVOLUTION_FABRIC_V18.md` and private `/MYRIAD-OMEGA/v1.8` Library ZIPs. Preserve all original evidence and dependencies.

## Two-cycle verified extension, appended to v1.9

- Live SOURCE checkout still exists only on draft UMBRA PR #21. Preserve branch and requalify at CURRENT HEAD.
- `research/EVOLUTION_V19_TRIBUNAL_AGGREGATE.json` now contains the **390,000-receipt two-hour** aggregate (eight independent subreports, zero failures, 36,833 quarantined candidates). Earlier 195k version is retained privately as the previous checkpoint.
- Actual SQLite evidence from two synthetic hours is split into three private file parts in Library `/MYRIAD-OMEGA/v1.9/two-hour-ledger/`, along with `MYRIAD_UMBRA_TWO_CYCLE_390000_ARCHIVE_PARTS.json` (all part SHA-256, overall ZIP SHA-256, source DB SHA-256). Reassemble in exact numeric order, verify SHA-256 and ZIP integrity, extract to private storage and keep original database read-only before resuming.
- The source `scripts/evolution_tribunal_v19.py` now supports row ranges beyond 195k and `aggregate --expected-count 390000`. The full two-hour receipt set passed every recomputation.
- 195k model-backed autonomous LLM workers, real trading intelligence, full original neural-bank restoration, public continuously deployed website, and MYRIAD-to-ICARUS merges remain unverified and blocked.
