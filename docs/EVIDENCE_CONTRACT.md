# UM-105 — Offline scientific evidence contract

## Purpose and authority
The independent `evidence-contract.mjs` module validates a **caller-supplied metadata manifest only**. It never fetches data, contacts a provider, reads storage or credentials, spends money, calls a broker, or changes the UMBRA simulation. It is deliberately not integrated into the existing world model, worker or UI. This is the first bounded, schema-only part of issue #6.

A schema-valid manifest receives `SCHEMA_VALID_RIGHTS_UNVERIFIED`, **not PASS for data quality, ownership, authenticity, license or scientific validation**. Even a manifest declaring `PUBLIC_DOMAIN` is only a claim. The digest is declared, not independently checked against source bytes. All returned records mark `externalValidation=false`, `rightsVerified=false`, `checksumVerified=false`, and `licensedDataFetched=false`.

## Strict v1 manifest
Exactly these own data properties are required, with no extras: `schema`, `provider`, `dataset`, `version`, `license`, `rights`, `retentionDays`, `redistribution`, `updateCadence`, `observedAt`, `capturedAt`, `validFrom`, `validTo`, `units`, `missingness`, `costUsd`, `authScope`, `revocation`, `sha256`. All properties are primitive; `validTo` alone may be null. A SHA-256-shaped string is **not** a signed attestation or verified checksum.

- `observedAt` = timestamp of the underlying observation, `capturedAt` = when the dataset was captured; require observation at or before capture.
- `validFrom` / `validTo` = claimed validity interval, with `validTo=null` for open-ended; a finite end must be strictly later than the start.
- All timestamps are strictly canonical UTC ISO-8601 with seconds and `Z`; no ambiguous timezone or silent local-time conversion.
- `rights`: `UNVERIFIED`, `PUBLIC_DOMAIN`, `LICENSED_RESEARCH`, or `RESTRICTED`; all **unverified declarations**.
- `redistribution`: `DENIED`, `METADATA_ONLY`, or `PERMITTED_UNVERIFIED`; all unverified declarations.
- `retentionDays` = integer 0–36500; `costUsd` = finite nonnegative declared amount up to 1,000,000, **not permission to incur any cost**.
- Text fields accept bounded ASCII identifiers (1–160 characters); no secrets, URLs with query credentials, markup or arbitrary nested data are accepted.

The validator inspects own property descriptors before reading values. It rejects getters, setters, unexpected keys, symbols, functions, nested objects and exotic prototypes. It does not serialize arbitrary input or invoke a user-supplied `toJSON`. It does not provide a general sandbox for hostile JavaScript proxies; callers should accept parsed JSON from a trusted local parser, never arbitrary executable objects.

## Validation maturity matrix

| Gate | Current state | Required future proof |
| --- | --- | --- |
| Schema structure | **TESTABLE** by local Node unit tests | Strict v1 manifest and adversarial fixtures |
| Data origin/authenticity | **BLOCKED** | Provider signature or independently authenticated retrieval |
| Rights and redistribution | **BLOCKED** | Verified provider license, terms, purpose, retention |
| Data checksum | **BLOCKED** | Hash actual bytes and match declared digest |
| Calibration | **BLOCKED** | Authorized datasets, units, predeclared calibration |
| Held-out predictive validity | **BLOCKED** | Frozen temporal split, naive baseline, proper score |
| Intervention identification | **BLOCKED** | Defensible identification assumptions and negative controls |
| Independent replication | **BLOCKED** | External implementation and independent datasets |
| Production/ethical authorization | **BLOCKED** | Explicit approval, rights and deployment review |

## Verification and handoff
Run `node --test tests/evidence-contract.test.mjs` and the full `npm test`. The ten dedicated tests include valid open/finite intervals, malformed timestamps, source/capture inversion, nonfinite amounts, unexpected fields, accessor and `toJSON` execution traps, and provenance nonclaims. Check the exact branch-head GitHub Actions result before acceptance; no real dataset has been imported or authenticated.

This module is independent of draft PRs #4, #7, #8, #9 and #11. It changes no existing browser assets, simulation versions, localStorage keys, public routes or hosted files. Integration with the live Living World, Decision Atlas and Focus Timer is **not authorized**; source/deployment provenance remains blocked in issue #5. Next possible bounded PR after review: independently authenticated source retrieval and rights verification, requiring explicit data-source authorization; **not** included here.
