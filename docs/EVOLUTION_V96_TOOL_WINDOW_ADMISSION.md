# v9.6 — authenticated at-most-once numerical tool admission

Actual v91 historical audit: three completed numerical receipts, two distinct verified seeds, one duplicate record; one completed reasoning receipt, zero jointly qualified tasks; all four authenticated, zero rejected. Duplicate group excluded from qualified tasks. Original receipts preserved.

v96 authenticates bounded history, excludes both completed and failed seeds, uses exclusive crash-conservative claims before inference, rejects malformed history and unsafe reparse paths, and requires >=2500 MiB physical, >=6000 MiB virtual, >=6 GiB disk and no resident model. Protected root assumption; no automatic marker deletion. Six local tests passed, including 24 concurrent contenders with one winner. Exact tested blobs c127601a75b4a29cb7f9cd44e144ad1de2842bd5 and c981625c087811604b8a6668902868cd1264a963. Run-level integration regressions added to CI; live rollout pending qualification and eligible idle window. Latest physical RAM 555 MiB, virtual 7587 MiB, disk 25.67 GiB. No relaxed guards, new live inference, private exports or production authority.

v94/v95 trained 12 isolated small synthetic candidates, 3600 optimizer steps. v94 negative and v95 positive controlled OOD outcomes retained, no promotion or live bank attribution. Eleven local combined training tests passed.
