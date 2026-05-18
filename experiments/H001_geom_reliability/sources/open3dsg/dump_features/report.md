# Open3DSG Feature Dump Audit

Status: `ready`
Generated: `2026-05-15T03:55:48+00:00`
ID strategy: `relationship_scan_split_suffix`
Feature root: `local_dataset/Open3DSG_staged/training_repro/output/features`
Selected run: `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3`

## Coverage

- Expected unique feature ids: 3900
- Complete ids across object embeddings, object valids, and relation embeddings: 3900
- Missing complete ids: 0
- Blockers: none

## Split Coverage

### train

- Expected unique ids: 3744
- Complete all roles: 3744
- Missing complete: 0
- Missing preprocessed: 0

### validation

- Expected unique ids: 156
- Complete all roles: 156
- Missing complete: 0
- Missing preprocessed: 0

## Feature Subdirs

- `export_obj_clip_emb_clip_OpenSeg_Topk_5_scales_3_vis_crit_0.19999999999999998_vis_crit_mask_0.1`: role `object_embeddings`, files 3900
- `export_obj_clip_valids`: role `object_valids`, files 3900
- `export_rel_clip_emb_clip_BLIP_Topk_5_scales_3_vis_crit_0.19999999999999998`: role `relation_embeddings`, files 3900
