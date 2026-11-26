# Cooperative resource reservation prototype

Uses exclusive PID-marker file creation in a trusted local directory, sorted group acquisition, rollback of only recorded owned markers, and identity/content checks before release. Pre-existing, stale, changed or missing markers are not automatically reclaimed. Actual UMBRA runtime uses PID marker files; this isolated primitive is not wired to that runtime, the claim broker or any scheduler. Multiple-file acquisition is not globally atomic, and filesystem path checks are not a security boundary against hostile concurrent replacement. Process-tree lifetime, real root identity, bootstrap/cache lock ordering, crash recovery and external admission require further qualification. No live locks acquired or released.

Local full suite 83/83 in 3.869s exit0, ten new tests, initial missing-module test failed. Dedicated cross-platform CI inherited. No live runtime, scheduler or DB mutation.
