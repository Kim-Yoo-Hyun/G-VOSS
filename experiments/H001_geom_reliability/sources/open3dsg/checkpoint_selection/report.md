# Open3DSG Checkpoint Selection

Status: `checkpoint_selection_ready_labeled_avg_blip_variant`
Created at: `2026-05-17T16:17:16+00:00`

## Fact

- The checkpoint provenance schema and selection policy are refreshed before any H001 held-out Open3DSG metric inspection.
- This artifact does not train Open3DSG, inspect held-out predictions, or compute metrics.
- Reduced-route checkpoints are smoke-only unless the paper claim is explicitly downgraded.

## Selection Gate

- Primary selection must not use H001 held-out metric results.
- Full-route checkpoints have priority over pilot checkpoints.
- A checkpoint can be paper-result eligible only after official feature audit, Docker preflight, provenance, and no-held-out-selection gates pass.

## Current Candidates

- checkpoint dir: `local_dataset/Open3DSG_staged/training_repro`
- candidate checkpoints: `8`
- paper-result eligible candidates: `0`
- labeled avg-BLIP variant candidates: `6`
- official feature audit status: `ready`
- train filter status: `filter_applied`
- validation filter status: `filter_applied`

## Selected Checkpoint

- path: `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt`
- source stage: `avg_blip_full_variant`
- selection role: `labeled_second_source_variant_candidate`
- selection reason: `documented lower-memory avg-BLIP full variant selected by Open3DSG train-dev val/loss after non-averaged BLIP route produced no checkpoint`
- train-dev val/loss: `0.32881081104278564` at step `13103`
- H001 held-out metrics seen before selection: `False`

## Claim Limitations

- `no_exact_official_non_avg_blip_checkpoint_after_documented_oom_attempts`
- `selected_checkpoint_is_averaged_blip_open3dsg_variant_not_exact_non_avg_open3dsg`
- `downstream_table_must_label_open3dsg_source_as_avg_blip_variant`

## Generated Files

- `selection_policy.json`
- `record_template.json`
- `manifest.json`
- `commands.md`
- `report.md`
