# Open3DSG Checkpoint Selection

Status: `checkpoint_selection_template_ready_checkpoint_missing`
Created at: `2026-05-09T15:44:01+00:00`

## Fact

- The checkpoint provenance schema and selection policy are frozen before Open3DSG checkpoint outputs are inspected.
- This artifact does not train Open3DSG, inspect held-out predictions, compute metrics, or select a real checkpoint.
- Reduced-route checkpoints are smoke-only unless the paper claim is explicitly downgraded.

## Selection Gate

- Primary selection must not use H001 held-out metric results.
- Full-route checkpoints have priority over pilot checkpoints.
- A checkpoint can be paper-result eligible only after official feature audit, Docker preflight, provenance, and no-held-out-selection gates pass.

## Current Candidates

- checkpoint dir: `local_dataset/Open3DSG_staged/training_repro/output/checkpoints`
- candidate checkpoints: `0`
- official feature audit status: `blocked`
- train filter status: `filter_applied`
- validation filter status: `filter_applied`

## Blockers

- `no_checkpoint_candidates`
- `official_feature_audit_not_ready:blocked`

## Generated Files

- `selection_policy.json`
- `record_template.json`
- `manifest.json`
- `commands.md`
- `report.md`
