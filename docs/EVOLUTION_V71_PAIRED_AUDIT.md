# MYRIAD v7.1 — paired scientific evaluation

Previous qualified head: 8de08b0d65e7b06b1082023e6362047ad6135c93 (24/24 returned PR workflows successful). Historical v1.3–v1.5 release matrix: reppiks490/builds, branch agent/myriad-omega-independent-handoff, myriad-omega-v15/docs/VERIFICATION_MATRIX.md. Historical full-host 3/13 is not current certification. Preserve integration lock and private artifacts.

The v6.7 wall-clock seed advanced 48 five-minute slots per four-hour scheduled interval, allowing the same family to repeat. Seed parity also fixed protocol order within each family. The new four-hour window index cycles four families and both orders over eight windows; repeated attempts in a single window use the same seed and are rejected by the cohort audit rather than counted twice. Historical receipts can still be replayed; completed receipts record actual result order, not an inferred legacy schedule.

The audit verifies each HMAC and replays scoring, rejects duplicate seeds, accounts for failed attempts, reports discordant cases and calculates a two-sided exact sign statistic on seed-level differences. This is descriptive: independence and generalization are unproven. No routing or promotion authority. Maximum 4096 receipts per audit; no raw model responses in output.

Windows isolated staging: RED missing new module (exit 1), GREEN 15/15 focused tests (exit 0), including v6.7 and v6.9 receipt tests. Live runtime unchanged; scheduler and telemetry last returned 0, neural twice-daily task had no recorded first run, no paired aggregate observed; free disk 29,015,306,240 bytes. No genuine new model trials, training weights, or algorithm-count increments asserted. New CI remains pending until checked at exact HEAD.

Next: verify CI, reconcile live source/launcher with versioned rollout and resource guards, execute an actual paired trial, validate authenticated private receipts, accumulate balanced cohort coverage, recover original weight banks and independently qualify release gates. No production merge/deploy, paid resources, or Codex.
