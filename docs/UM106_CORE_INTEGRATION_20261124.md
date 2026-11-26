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
