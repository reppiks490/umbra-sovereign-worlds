# MYRIAD v3.6 ? bounded model-backed worker expansion
Extends the existing v2.6 persistent queue without deleting or resetting workers.
Enrollment is idempotent and bounded to 4096 logical IDs. The local deployment
starts at 128 hourly identities, each invoking the digest-pinned shared Qwen3 1.7B
model. This does not create 128 independent model weight sets.
A batch reuses the model for 45 seconds, keeps native v3.3 token and thread limits,
and checks free memory, disk space and evidence quota. The time budget is a soft
admission budget checked between bounded chunks, not a hard cancellation guarantee.
Windows scheduler must prevent overlapping invocations. Raw evidence remains
private; production authority and neural training claims remain false.
Actual hourly completion must be measured separately. Tests exercise idempotent
expansion, old-state preservation, limits and resource admission without live inference.
