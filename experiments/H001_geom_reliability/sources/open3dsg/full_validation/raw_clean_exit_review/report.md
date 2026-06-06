# Open3DSG Raw Provenance Review

Status: `open3dsg_raw_provenance_review_ready`
Mode: `full_validation_clean_exit`
Created at: `2026-06-06T11:59:04+00:00`

## Claim Boundary

This review concerns provenance polish for the unmodified 533/548 Open3DSG full-validation branch. The paper-facing primary Open3DSG route remains the 548/548 recovery branch, whose raw dump already has clean-exit provenance.

## Full-Validation Clean-Exit Review

- unmodified route coverage: `533/548`
- unmodified raw rows: `26746`
- unmodified process exit: `137`
- primary recovery coverage: `548/548`
- primary recovery raw rows: `26938`
- retry artifact status: `not_evaluable_retry_artifact_missing`
- reduce unmodified exit-137 caveat: `False`

## Decision

Keep the unmodified 533/548 branch as sensitivity evidence with post-finalization exit-137 caveat. Use the 548/548 recovery branch as the main Open3DSG full-validation result with its recovery-policy caveat.

## Blockers

- `retry_artifact_missing_no_clean_exit_replacement`
