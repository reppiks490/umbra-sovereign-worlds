"""Conservative disk admission for source-only native training.

Preserve the 7.8 GB operating floor after reserving bounded training writes.
An outstanding bootstrap reservation must still pass its independent owner gate;
callers with a known remainder can supply outstanding_bootstrap_bytes.
"""
MIN_FREE_AFTER_TRAINING = 7_800_000_000
TRAINING_WRITE_RESERVE = 400_000_000


def training_storage_admitted(free_bytes, planned_growth_bytes=TRAINING_WRITE_RESERVE,
                              outstanding_bootstrap_bytes=0):
    values = (free_bytes, planned_growth_bytes, outstanding_bootstrap_bytes)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("invalid storage admission budget")
    return free_bytes >= MIN_FREE_AFTER_TRAINING + planned_growth_bytes + outstanding_bootstrap_bytes
