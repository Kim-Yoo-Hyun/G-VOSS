# Open3DSG Checkpoint Selection

Status: `checkpoint_selection_ready_official_non_avg_blip`
Created at: `2026-06-04T08:24:04+00:00`

## Fact

- The checkpoint provenance schema and selection policy use route priority, source provenance, and Open3DSG train-dev validation loss only.
- For the selected route, no H001 held-out metric, failure taxonomy, or visual inspection is used for checkpoint selection.
- This artifact does not train Open3DSG, inspect held-out predictions, or compute metrics.
- Reduced-route checkpoints are smoke-only unless the paper claim is explicitly downgraded.

## Selection Gate

- Primary selection must not use H001 held-out metric results.
- Full-route checkpoints have priority over pilot checkpoints.
- A checkpoint can be paper-result eligible only after official feature audit, Docker preflight, provenance, and no-held-out-selection gates pass.

## Current Candidates

- checkpoint dir: `local_dataset/Open3DSG_staged/training_repro`
- candidate checkpoints: `14`
- paper-result eligible candidates: `6`
- labeled avg-BLIP variant candidates: `6`
- official feature audit status: `ready`
- train filter status: `filter_applied`
- validation filter status: `filter_applied`

## Selected Checkpoint

- path: `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`
- source stage: `official_non_avg_blip_full`
- selection role: `primary_candidate`
- selection reason: `predeclared official full-route checkpoint selected by Open3DSG train-dev val/loss`
- train-dev val/loss: `0.5724539160728455` at step `13103`
- H001 held-out metrics seen before selection: `False`

## Route Comparison

- best official non-avg BLIP: `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`, val/loss `0.5724539160728455` at step `13103`
- best avg-BLIP variant: `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt`, val/loss `0.32881081104278564` at step `13103`
- non-avg minus avg train-dev val/loss: `0.24364310503005981`
- official non-avg BLIP route completed, but its train-dev val/loss is worse than the existing avg-BLIP variant
- avg-BLIP checkpoint-route caveat can be reduced only after the full downstream H001 Open3DSG chain is regenerated under non-avg output paths
- current avg-BLIP H001 metric tables remain the active paper evidence until non-avg raw dump, adapter, geometry join, metrics, CI, and caveat wording exist

## Claim Limitations

- `non_avg_checkpoint_selected_no_downstream_h001_metrics_yet`
- `current_paper_tables_still_use_avg_blip_until_non_avg_downstream_chain_is_regenerated`
- `non_avg_train_dev_val_loss_worse_than_existing_avg_blip_variant`

## Generated Files

- `selection_policy.json`
- `record_template.json`
- `manifest.json`
- `commands.md`
- `report.md`
