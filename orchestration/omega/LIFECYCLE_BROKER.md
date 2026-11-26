# Authenticated lifecycle prototype

Extends the isolated claim prototype with atomic broker lease provenance, separately signed worker reports and reviewer approvals, distinct role/lane authorization, exact receipt and lease binding, replay protection across actions/restarts, and evidence revalidation. Legacy claims/reports cannot enter the signed lifecycle. External resources and process handles are explicitly refused. Test keys are fixtures. This is not a live authorization boundary: direct DB/legacy method access remains possible, no protected server or production key management exists, and independent reviewer identity is not established. No active DB, scheduler, runtime or deployment mutation.

Local full suite 73/73 in 3.702s exit 0, 12 new tests. Initial missing-module test failed. Dedicated CI inherited; qualify exact head separately.
