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
