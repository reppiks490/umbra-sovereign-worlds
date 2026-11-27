# UM-106 integrated core qualification — 2026-11-24

Base main: b18d8a1a68a46f634b7daf035ed07ff579b275e1. This is an independent draft integration lane, not a production merge. All original PR branches and commits remain intact.

## Reconciled lanes

- PR #14: finite integer ensemble dimensions; engine and regression blobs imported exactly.
- PR #16: fail-closed civic residuals and malformed collection checks; additional sparse-collection rejection.
- PR #22: dense settlement validation; cross-lane repair makes G06 safe when civic collections are absent, blocks unsafe replay, and preserves detection of finite negative resource divergence. G07 compares selected rounded state, not a full canonical checkpoint.
- PR #24: independent placebo simulator calls, exact replay helper and CLI regression. Old cached placebo receipts require independent requalification.
- PR #12: offline evidence contract and tests; no live provider access.
- PR #13: corrected workflow parser, read-only permissions and non-cancelling evidence; retained main's existing schedule, 16-minute unit budget and 300-case checks; browser timeout 25 minutes. The contract test permits a bounded 20-minute unit maximum.

## Verification

Individual PR #24 verification passed. PR #21 remains separate with 24/24 reported workflow runs. PR #13's new revision had no PR-triggered run at latest inspection; do not label it green. Combined core cross-lane regression was RED 3/5 failures against exact PR22 Court and extracted PR16 audit, GREEN 5/5 against corrected implementation, using a deterministic fixture engine (not the actual full engine). Court source and regression test committed with exact tested blob matches. CI contract RED two failures, GREEN 4/4 against exact main-derived workflow and viewport fixture. Both committed blobs matched tested bytes. Full engine, 300-case, advanced registry and real browser verification remain pending until exact-head CI is observed.

## Remaining work

Integrate archive #4, served worker #7, research tournament #8, visualization #9, takeover docs #11 and independently qualify their combined behavior. Preserve MYRIAD #21 as a separate draft research lane; do not merge research into production automatically. Original live website is separate. No deployment, external data acquisition, financial account access or production promotion.

## UM-106 replay-bound integration — 2026-11-26

Parent c9c682db768dd35fca411dd5bdadcdad23cbb8df; UM-110 source bc1cf1ad727fc5de95851cb434fb5125307aa4da; native Windows Node v26.13.0. Exact 39 source/test/data blobs verified before execution. Full Node suite with --test-concurrency=1 --test-reporter=tap: RED 63/74 (11 replay regressions, exit 1, 4.359 s), GREEN 74/74 (0 skipped, exit 0, 4.609 s). RED log SHA256 38edb3ef01e24b174713607775a47b0549c052c653d099a2a706ea1023f19fae; GREEN 554529c30134d5cd73579ff82de852886b562210ddfbb2777f26b33ad8ebc130. Candidate Court Git blob 3ccd3a58e494ff622f38a8e76861c362b14a6baa; imported test blob 9f10ba48edd468e8820bcd84a77b75a0f92ecc7c. Initial Node 26 default reporter produced readable failures but failed TAP parsing; rerun explicitly selected TAP. No source-engine, civic, browser or workflow changes. These are native software tests, not browser, scientific or model qualification. Workflow inventory: 5,307 files, untruncated; branch differs from audited main only in unit.yml, inspected for normal Node/Chromium verification. No workflow edits. Exact-head CI and served/mobile verification remain separate gates.


## 2026-11-27 ? source-pinned archive, research and worker verification integration

Baseline: b5c70f2bd451a60df88e156e08ba3a5083d15699.
Imported the following owning-PR source, tests and dedicated documentation without overwriting shared engine, civic audit or knowledge-layer files:
- PR #4: 437304a74e3465ef1084cc429db0fae6a44c5159 (archive.mjs, tests/archive.test.mjs, docs/ARCHIVE.md).
- PR #8: 1699d7eedea836c2b3fd4d67b6925463787db0a3 (research.mjs, tests/research.test.mjs, docs/RESEARCH.md).
- PR #7: fb5fc3ca589801f00252ecc8b60bf97f6e1618ce (tests/served_smoke.py).

Combined changes: preserve existing bounded unit workflow and add served browser test step; add cross-lane archive/Court/research regression and CI contract check. Court policy serialization now uses sorted own policy keys so canonical archive hydration cannot trigger a false selected-state replay failure. No simulation rules changed.

Native Windows failing-first: focused integration 5/7 (missing served CI step and false G07 replay mismatch); after repair 7/7. Complete npm test 105/105, zero failures or skips, diff check clean. Combined browser launch was refused by the workstation RAM admission gate before Chromium started; dedicated browser evidence remains pending. Source branches remain intact; no merge into main, deployment, model execution or live authority change. PR #9 separate UI lane is not included in this commit.

## 2026-11-27 — planetary lens and evidence boundary integration

Source-pinned PR #9 7b71f16eac35063ec56c2675677c3e334dcdec44 (index.html, observatory.mjs, world.css, tests/smoke.py, docs/PLANET_LENSES.md) and PR #12 62d82f337bbcbf5d235ec66ceacc429b3ecb8620 (evidence-contract.mjs, tests/evidence-contract.test.mjs). Before importing, exact file comparisons showed no divergence against the original UI base and preceding evidence head. Native combined npm test 106/106, zero skips/failures; diff check passed. PR #9 separately passed four actual Chromium viewport/reduced-motion cases. Combined served browser qualification remains pending; this is not main or deployment.


## 2026-11-27 ? paired seed and exact topology reconciliation

Sources: PR #14 4851f48db2ab418c435eb7ae133a6b54496e74ab and PR #22 1a7358b7f1e523870ca06fbe93f09698bbae22a7. Imported exact new regressions and narrowly applied source hunks; retained the integrated civic validity/settlement guards and archive-compatible sorted policy summary. Combined RED 0/3, GREEN 3/3. Full native Windows Node 109/109, zero failures/skips, diff check passed. Strict paired seed contract is nonzero uint32. G01 requires dense topology and valid geometry/neighbor maps; G07 blocks malformed topology and compares seeded topology. No engine rules changed for valid seeds, no main merge or deployment.

Native stack compatibility against prior core eb8e9c8: exact #26, #27 and cumulative #33 source tests passed 30/30 Node and 5/5 Python acquisition policy tests. This is fixture and actual synthetic simulator evidence, not live model inference, checkpoint evaluation, hosted transport or production authority.
