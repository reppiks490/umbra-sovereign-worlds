# UMBRA Ω v5 — The Living Accord

## Provenance and scope

**Before:** v4 allowed deterministic ecology, adjustable policies, paired synthetic experiments and timeline exploration.

**Change:** added `society.mjs` with 42 civic councils, four synthetic factions, periodic elections, diplomatic corridors, reciprocal aid, local taxation/grant spending, account-level residuals and an auditable transfer journal. Added seven-axis sensitivity experiments in `engine.mjs`, interactive civic network/timeline and ledger in `observatory.mjs`, independently replayed Reality Court (`court.mjs`), Node and Chromium tests.

**Now:** a locally runnable, instrumented browser app supporting model-internal interventions, mechanical sensitivity, civic accounting, replay and clear blocked scientific validation gates. No hosted services, real independent agents, credentialed integrations, real civic/economic calibration, or external trust attestations.

## Invariants

- Models have keyed deterministic stochasticity; identical seed+policy+turn count implies identical state.
- Civic fiscal transfer deltas reconcile settlement wealth and council treasury changes **within the civic step**; food aid transfers preserve the modeled units within the civic step. The base ecological model *does* produce and consume food/wealth.
- Site populations and resource values remain finite and nonnegative under tested stress seeds.
- Policy sensitivity uses identical seed grids and exogenous draws to reduce paired variance; displayed intervals are **within-model replicate percentiles**, not credible intervals for the real world.
- Reality Court labels engineering tests separately from empirical/scientific validation.

## Execution

```bash
npm test
python -m pip install playwright
python -m playwright install chromium
python tests/smoke.py
python -m http.server 8080
```

## Worker ownership

- Simulation architect: `engine.mjs`, `society.mjs`, `tests/*.test.mjs` (do not edit frontend concurrently).
- Observatory engineer: `index.html`, `world.css`, `observatory.mjs`, browser regression (coordinate worker protocol changes).
- Verification/research: `court.mjs`, `docs/MODEL_CARD.md`, `docs/PROTOCOL.md`, release verification and source-rights gates.
- Changes to shared contracts require coordinating before implementation, not running conflicting writers.

## Next scientific gates

Versioned scenario commitments, comprehensive generated-event audit, credible calibration to external datasets under permission, worker cancellation and resource caps, real end-to-end served module test, persistent shared-world hosting only with explicit authority.
