# Open3DSG Feature Dump Audit

Status: `blocked`
Generated: `2026-06-04T13:24:35+00:00`
ID strategy: `relationship_scan_split_suffix`
Feature root: `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features`
Selected run: `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_official_blip_top5_scales3`

## Coverage

- Expected unique feature ids: 533
- Complete ids across object embeddings, object valids, and relation embeddings: 533
- Missing complete ids: 0
- Blockers: `validation_missing_preprocessed:15`

## Split Coverage

### train

- Expected unique ids: 0
- Complete all roles: 0
- Missing complete: 0
- Missing preprocessed: 0

### validation

- Expected unique ids: 533
- Complete all roles: 533
- Missing complete: 0
- Missing preprocessed: 15

## Feature Subdirs

- `export_obj_clip_emb_clip_OpenSeg_Topk_5_scales_3_vis_crit_0.19999999999999998_vis_crit_mask_0.1`: role `object_embeddings`, files 533
- `export_obj_clip_valids`: role `object_valids`, files 533
- `export_rel_clip_emb_clip_BLIP_Topk_5_scales_3_vis_crit_0.19999999999999998`: role `relation_embeddings`, files 533
