# Read-only OMEGA queue observation

Projects lane-local task IDs, states, scores and advisory eligibility from an existing SQLite ledger using mode=ro and query_only. Includes cross-lane dependency and resource occupancy checks; reported tasks keep resources busy. No lease token, owner, handle, reason, objective or evidence paths are returned. A candidate is not actual admission or permission; runtime resource locks, branch ownership and independent review remain required. The file must already exist. No scheduling, database mutations, task claims, external dispatch or deployment.

Full local suite 37/37 passed (1.042s, exit 0), including six new tests using actual temporary SQLite files. The new module test failed initially because the module did not exist. Dedicated cross-platform CI was introduced in parent PR44; wait for exact-head results on this child. No live activation.
