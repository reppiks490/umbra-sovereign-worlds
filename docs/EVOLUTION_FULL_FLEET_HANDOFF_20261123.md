# MYRIAD Ω × UMBRA Evolution Fabric v1.8 — Verified handoff (2026-11-23)

## Authoritative source and release status
- Review branch: `agent/evolution-fabric-v18-research` in `reppiks490/umbra-sovereign-worlds`.
- Draft review: https://github.com/reppiks490/umbra-sovereign-worlds/pull/21
- The last source+CI qualification SHA was `bcd82cc9782795e51fe4f6a474e293adeda0c764`: evolution verification run `45260714600` SUCCESS; preexisting 5,000-case suite `45260714459` SUCCESS.
- This report and handoff documentation were committed later; always validate **current** HEAD before merge.
- Keep UMBRA `main` and ICARUS OMNIGENESIS PR #503 unmodified pending MYRIAD 13/13 independent release gates and explicit owner approval. No broker execution, source promotions, or Codex-backed scheduled tasks.

## Audited local executable milestone
- 250,000 fully enumerable *parameterized synthetic experiment configurations*, organized around **25 implemented optimizer/operator combinations** and 100 synthetic regimes × 100 objectives. Not 250,000 independent sourced algorithm codebases.
- 195,000 persistent independent **logical workflow identities**, each assigned and evaluated during one *synthetic policy* sweep (not 195,000 OS processes or simultaneous model-generation sessions).
- Audit: 195,000 unique recorded workflow IDs, 2,340,000 optimizer steps, 18,402 quarantined synthetic improvement proposals, 194,987 peer exchange records, zero processing failures, SQLite integrity `ok`. Mean 696 records/s, peak RSS 359.4 MB. Receipt aggregate: `b575aa674b54dbe82759a5c9b789bd100fe13ed877d5129c3c6b451e0461ecb2`.
- Full result `research/EVOLUTION_FULL_FLEET_SYNTHETIC_AUDIT_20261123.json` stores reported metrics, sample receipts and audit script's initial source SHA. The actual audit used the locally staged indexed scheduler; the initial source SHA is *not* proof that the full data ledger was generated with the original unpatched commit.
- Complete auditable SQLite ledger (324 MiB raw), compressed to approx. 69 MB, and SHA256 file manifest are **not in public GitHub**. Saved in private user ChatGPT Library `/MYRIAD-OMEGA/v1.8/MYRIAD_UMBRA_195000_SYNTHETIC_AUDIT_LEDGER.zip`. Private source and ten-agent candidate archives also stored in that folder.
- The ten recovered 411,000-weight agent networks and 10,000 lightweight ability adapters were the ONLY original preserved neural weights actually available. The ten agent networks received three real PyTorch synthetic gradient updates and were saved as **quarantined candidates**, original weights unchanged. This full fleet sweep trained **zero further neural networks**.

## Weight-bank lineage
- Historical total 8.22 GB (agent FP16) and 640 MB (ability FP16) were described and hashed in an earlier execution host, but **full trained raw files and original SQLite ledgers are not currently accessible**. Do not recreate random weights and call them original.
- `scripts/myriad_bank_fabric.py` validates source and lineage and defines non-destructive **30GB agent / 10GB ability** expansion geometry. These are **unallocated/untrained capacity targets**, not new verified model weights. It also proposes 64GB replay, 16GB causal and 8GB retrieval stores.
- The sourced methods registry currently contains 101 **metadata** references from 13 sources, with 25 local algorithm/operator combinations. Do not describe these as 250,000 independently implemented algorithms or licensed third-party code.

## Runtime / website
- Animated read-only website under `evolution/`; local Python HTTP server `python3 scripts/evolution_api.py --port 8797`. Mobile browser on user's machine requires properly authenticated secure remote hosting; localhost is not public.
- Persistent scheduler: `python3 scripts/evolution_scheduler.py --db /path/to/mesh.sqlite3 init` and `python3 scripts/evolution_scheduler.py --db /path/to/mesh.sqlite3 run --max-jobs 128 --steps 12`. Inspect status after.
- Repository Actions `umbra-evolution-mesh-hourly.yml` is **off** unless opt-in flag `UMBRA_EVOLUTION_ENABLED` is set, and is bounded to a 256-case diagnostic sample, not full hourly 195k neural worker service.
- New isolated Railway project `MYRIAD Evolution Observatory` was created. Initial GitHub deployment failed because Railway's linked account **lacks authorization** to read `reppiks490/umbra-sovereign-worlds`; it has no running public deployment. Do not invent a URL. The user must authorize this repository through Railway before retrying.
- No Supabase projects exist in the connected Supabase account.

## Next independent engineering gates
1. Revalidate code and receipt hashes; run CI on current HEAD. Archive full checkpoint bytes+ledgers privately and verify their original training receipts before expanding trained banks.
2. Implement and benchmark sourced algorithms as independent code (license tracking, reproducibility, anti-overfit), distinguishing distinct algorithms from parameter variants.
3. Deploy first isolated authenticated hosted observatory; test actual iPhone access and traceable server data, with cost ceilings.
4. Benchmark real model-backed workers with hard compute budgets, persistent distributed queues, time-window SLA monitoring, cross-worker learning review and no automatic unreviewed merges.
5. Only after MYRIAD's 13/13 release gates and independent review propose read-only ICARUS adapters pinned to exact SHAs and request owner release authorization.

Never call this a production 195,000-agent self-improving intelligence system or claim hourly SLA until independently demonstrated.
