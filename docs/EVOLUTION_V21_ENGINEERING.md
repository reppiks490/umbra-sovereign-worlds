# MYRIAD Ω × UMBRA — v2.1 parent-evidence lineage and auditable collaboration

**Status:** Research-only source on UMBRA draft PR #21. This phase provides **explicit parent-receipt attribution** for future synthetic worker research. No neural-network fine-tuning, real-world intelligence certification, production merges, or trading authorization.

## What changed

1. `umbra_evolution_mesh.peer_evidence_for` now returns the verified prior-hour peer's worker identity, UTC logical hour, SHA-256 digest, source domain and bounded synthetic parameter vector. The old `peer_for()` accessor remains for compatibility.
2. `run_batch` and the persistent `evolution_scheduler.process()` seal `peer_provenance_schema='umbra.evolution.parent_link.v21'` and a `peer_parent` object in every **new** record, or explicit `null` if no eligible parent exists. The child digest covers both.
3. `evolution_lineage_v21.py` independently rechecks child synthetic scores, resolves the referenced parent from SQLite using primary keys, verifies that parent's original receipt and heldout/stress qualification, refuses same-hour/future/self/cross-domain dependencies, and distinguishes `verified_prior_hour`, `no_prior_parent`, `legacy_unproven`, and `legacy_no_peer` records.
4. Future parent parameter assimilation uses evidence from a candidate that passed a replayed heldout/stress gate. A self-reported review flag plus a newly computed hash is **not sufficient**.
5. Seven regression tests exercise actual `run_batch` write/read integration, legitimate parent linkage, missing parent, fake digest, same-hour dependency, old records with missing provenance, and explicit no-parent cases.

## Historical 390,000-record audit — important correction

The original archival database was restored **read-only** from its independently checksum-verified three-part ZIP. SQLite returned the following **exact counts**:

| Stored evidence class | Number |
|---|---:|
| Total completed synthetic research occurrences | 390,000 |
| Records with `peer_used = true` | 389,987 |
| Records with `peer_used = false` | 13 |
| Records with explicit parent-receipt provenance schema | **0** |

Every earlier record passed the *existing numerical receipt replay* in the prior v1.9 tribunal. That does **not** establish that the historical `peer_used` boolean was causally justified by an independently qualified, earlier source.

A fresh v2.1 lineage audit of **3,000 archived records** (1,500 from each synthetic hour) found **zero malformed receipts**, but classified **2,987 `legacy_unproven` peer links and 13 `legacy_no_peer` records**. Do not extrapolate that sample into an independent proof for the entire archive; the full database-level 389,987/13 count is a direct read of the stored metadata, not a replay of all parent edges.

**This is why v2.1 introduces parent hashes.** Do not silently retrofit historical records, invent missing sources, or equate same-hour data reuse with longitudinal learning.

## New source contracts

```json
{
  "peer_provenance_schema": "umbra.evolution.parent_link.v21",
  "peer_used": true,
  "peer_parent": {
    "parent_workflow": "E000014",
    "parent_hour": "2026-11-23T18",
    "parent_receipt_sha256": "<exact prior-hour source SHA-256>",
    "parent_domain": "ecology"
  }
}
```

`parent_hour` must be strictly earlier than the child hour; `parent_domain` must match the child for parameter assimilation. Cross-domain research evidence may be **read and compared** through the existing v1.9 collaboration tribunal, but its parameters cannot silently enter a foreign domain's trainer.

## Reproduce

```bash
python3 -m unittest discover -s tests -p 'test_evolution_lineage_v21.py' -v
python3 scripts/evolution_lineage_v21.py --ledger /private/read-only/evolution_fleet_195000_evidence.sqlite3 --start-row 1 --limit 1500 --output /empty/path/lineage_1.json
python3 scripts/evolution_lineage_v21.py --ledger /private/read-only/evolution_fleet_195000_evidence.sqlite3 --start-row 195001 --limit 1500 --output /empty/path/lineage_2.json
```

Archive format and independent SHA-256 recovery procedure: `docs/EVOLUTION_V20_ENGINEERING.md`. Full raw data stay private under `/MYRIAD-OMEGA/v1.9/two-hour-ledger/` in the user's ChatGPT Library. A checksum is an integrity property, not an identity signature or independent ground truth.

## Next: stronger collaboration, actual models, and verified discovery

- Validate every candidate's immutable parent DAG and store an explicit evaluator version, source data provenance, optimizer version, cost and holdout partition receipts. Add anti-leakage and benchmark contamination audits.
- Implement a bounded first actual **authenticated model-backed worker** on an explicit opt-in endpoint with a monetary/token ceiling. No present claims of thousands of simultaneously connected inference models are justified.
- Independently source and implement more algorithm families with license provenance. There are now 19 executable optimizers against 250,000 parameterized synthetic configurations; **not** 250,000 independently engineered algorithm implementations.
- Retain MYRIAD's 13/13 release gates and require explicit owner authorization before any reviewed UMBRA-main / ICARUS-OMNIGENESIS integration. Do not use Codex in scheduled tasks.
