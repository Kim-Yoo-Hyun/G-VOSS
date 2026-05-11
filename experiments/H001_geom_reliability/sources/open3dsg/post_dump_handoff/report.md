# Open3DSG Post-Dump Handoff

Status: `waiting_for_feature_dump_completion`
Created at: `2026-05-10T15:57:57+00:00`

## Feature Progress

- feature run: `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3`
- complete feature ids: `1932/3900`
- progress: `49.54%`
- missing complete ids: `1968`

## Gates

- `feature_dump_complete`: `False`
  blockers: `object_embeddings:1932/3900, object_valids:1932/3900, relation_embeddings:1932/3900, complete_all_roles:1932/3900`
- `official_feature_audit`: `False`
- `checkpoint_available`: `False`
- `raw_dump_available`: `False`
- `adapter_ready`: `False`
- `metrics_ready`: `False`

## Transition Rule

The current handoff is a reproducibility/claim-boundary artifact only. It does not train Open3DSG, create a checkpoint, inspect metric failures, or create paper-result evidence.

Real Open3DSG second-source claims remain blocked until feature audit, checkpoint reproduction, identity-preserving raw dump, prediction JSONL export, geometry join, metric run, and locked-schema failure-analysis rows are complete.
