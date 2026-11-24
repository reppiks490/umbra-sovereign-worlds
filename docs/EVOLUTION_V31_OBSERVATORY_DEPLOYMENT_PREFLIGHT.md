# MYRIAD Ω v3.1 — Observability startup repair, bounded preflight, no production deployment

**Scope:** source-only improvement to the read-only MYRIAD/UMBRA evolution observatory Docker image, plus one live API diagnosis recorded as a *sanitized audit*. GitHub draft PR #21 remains a research review; no UMBRA main merge, ICARUS PR change, cloud service mutation, public domain exposure, live models or Codex scheduling.

## Live Railway build failure — not hypothetical

The connected Railway project `MYRIAD Evolution Observatory` exposes service `evolution-observatory`. Its production deployment `ec6c91ef-f3b4-4442-af4f-ceb98220165c` is in status `FAILED`, originating from UMBRA main commit `7cb56801795b1f9bc590a9ec1bc3ffeadab7362f` (not this research branch). Railway build logs show `BUILD_IMAGE`, builder `RAILPACK`, and `No start command detected`. The service had `evolution/Dockerfile` configured as a path, but the builder still selected RAILPACK. No application image started and therefore no live `/api/health` passed. The service has no verified public observatory URL.

**Builder repair is still required at the Railway service level**: select `DOCKERFILE` and the correct `evolution/Dockerfile` path, then build a private preview, inspect logs, and verify health. This change is **not** performed by a code-only commit. Do not imply the failed Railway production deployment is fixed.

## v3.1 executable fix

- `evolution/Dockerfile` now starts Python through a shell that reads Railway's assigned `${PORT:-8797}` rather than assuming the fallback port. Its Docker `HEALTHCHECK` also reads `PORT` from the runtime environment. Port `8797` remains a documented local default and exposed advisory port.
- The original v1.8 Docker COPY line omitted `evolution_algorithms_v19.py` (imported by the current v1.9 API) and the v1.9 tribunal summary. Both resources are now explicitly copied, preventing a missing import and a silent absent-report response.
- No changes were made to `scripts/evolution_api.py`, preserving the read-only behavior. It already supports explicit `--host` and `--port` flags, returns `/api/health` and denies POST/PUT/DELETE. Exposing this service publicly still requires an owner-approved access-control proxy and release review.
- `scripts/evolution_railway_preflight_v31.py` examines **sanitized service builder metadata** read previously from the real Railway API. It classifies the known RAILPACK mismatch as `BLOCKED_BUILDER_MISMATCH`; even a correctly configured Dockerfile builder is `PREVIEW_CANDIDATE_ONLY` until a build and runtime checks have passed. It makes no network connection or deployment mutation.
- **Seven local `unittest` checks** include builder mismatch, correct-but-unapproved builder, Dockerfile dynamic-port source check, invalid/untrusted builder rejection, and actual bound loopback HTTP server startup. `/api/health` returned HTTP 200 and read-only true; POST returned HTTP 403. A minimal reconstructed Docker `COPY` filesystem successfully served `/api/methods` and `/api/tribunal` without any extra repository files; this still is **not** an actual Docker build. The Docker image itself has **not** been built, and the Railway service still has its previous failed deployment.

## Owner-authorized release sequence (not performed)

1. Confirm the production service and authorized environment; inspect all staged changes and estimate expenses. Do not automatically accept production patches or publish a public URL.
2. Select the Dockerfile builder through the supported Railway service configuration process, retaining the branch until independent release gates pass.
3. Build in a preview/staging environment, use its assigned `PORT`, and check HTTP `/api/health`, runtime logs, read-only metrics and absence of secrets. Add authentication for remote access.
4. Only after MYRIAD's independent 13/13 release gates and explicit owner approval consider public production rollout. **Do not make scheduled Codex jobs.**

## Reproduction

```bash
python3 -m unittest discover -s tests -p 'test_evolution_railway_preflight_v31.py' -v
python3 scripts/evolution_railway_preflight_v31.py \
 --redacted-service-json /private/current-railway-service.json
```

The JSON should contain only `builder`, `dockerfilePath`, and `healthcheckPath`; do not include environment variable values, credentials, tokens, hosted domains or user account details.

## Transitive source-manifest repair

The v3.1 Dockerfile modification necessarily updates `EVOLUTION_V18_SOURCE_MANIFEST.json`. That historical review file is itself pinned by `EVOLUTION_V23_SOURCE_MANIFEST.json`, so the older checkpoint CI detected the stale pinned digest. We reproduced the exact mismatch before changing it, then updated **only** v2.3’s manifest entry for v1.8 and included both historical manifests in the v3.1 CI chain. Neither v2.3 application code nor the original checkpoint weights were changed.
