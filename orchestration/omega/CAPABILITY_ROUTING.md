# Advisory capability routing

Adds a deterministic selector that intersects a discovered registry, lane routing, explicit read-only action policy, intent, rank, and latest fresh execution evidence metadata. Rejects stale, future, conflicting, failed, absent or invalid digest metadata; never dispatches a connector or grants authority. A receipt digest string is not authentication; callers must independently verify receipt bytes and provenance before use. No live scheduler changes, no mutation routes and no external account data included.

Local full orchestration suite passed 23/23 in 0.947s, including eight new routing tests. Original registry metadata validation observed 2,420 action identities and 73 connector namespaces; this is not a verified execution count. The initial missing-module test failed before implementation. No independent reviewer available; no production activation.
