# Native transfer resume correction

Scope: preserve downloaded bytes and prevent repeated short-range transport failures from exhausting all retries on the original 16 MiB requests. Start at 4 MiB; halve the range on recoverable ranged-transfer errors down to 1 MiB. Exact range validation, storage checks, bounded retries, fsync, pinned digest and no-overwrite promotion remain unchanged.

Regression: a deterministic truncating transport fails the old default; the corrected implementation completes and validates the same bytes. A no-progress transport still exhausts its bounded retry count without promoting a partial file.

Owner-local equivalent patch qualification: 9 focused Python tests, 245 full Python tests in the CPU PyTorch environment, and 193 Node tests passed. The corrected downloader has been observed resuming the actual transfer. Final network completion and model receipt remain pending; CI for this review branch is independent and must be checked at its exact head. No new model-training or production authority is asserted.

Review this branch against the AUTOGENESIS feature branch (PR #34), not main. Do not revert the active local release or interrupt an active bootstrap. Preserve existing scheduler, source licensing and storage controls.
