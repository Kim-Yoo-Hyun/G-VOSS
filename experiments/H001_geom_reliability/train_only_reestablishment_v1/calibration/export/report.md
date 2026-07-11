# Calibration Export

Created at: `2026-07-10`
Split name: `train_only_reestablishment_v1`
Status: `ready`

## Inputs

- Subset source: `local_dataset/3DSSG_subset/relationships_train.json`
- Selected scans file: `experiments/H001_geom_reliability/train_only_reestablishment_v1/splits/method_development_scans.txt`
- Geometry sources: `semseg_obb_v0`

## Outputs

- Table: `table.jsonl`
- Negatives: `negatives.jsonl`
- Manifest: `manifest.json`

## Counts

- Scans: `1173`
- Subgraphs: `3765`
- Positive rows: `28977`
- Negative rows: `37477`
- Uncertain rows: `0`

## Families

- `proximity`: `23008`
- `relative_vertical`: `5488`
- `support_contact`: `37958`

## Candidate Sources

- `counterfactual_negative`: `37477`
- `gt_positive`: `28977`

## Negative Strategies

- `proximity_far_pair`: `10528`
- `support_replace_object_far_or_incompatible`: `24792`
- `support_replace_subject_floating`: `331`
- `vertical_invert_higher_lower`: `1826`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `11`

### Warnings

- `invalid_obb:aa20278c-8bc8-2c5b-9d18-016312e4463a:50:non_positive_aabb_extent`
- `invalid_obb:c92fb5a9-f771-2064-86fc-ae25bdd558c4:22:non_positive_aabb_extent`
- `invalid_obb:20c993af-698f-29c5-84b2-972451f94cfb:10:non_positive_aabb_extent`
- `invalid_obb:bf9a3deb-45a5-2e80-8291-f0039d671ea1:14:non_positive_aabb_extent`
- `invalid_obb:4fbad31a-465b-2a5d-8566-f4e4845c1a78:12:non_positive_aabb_extent`
- `invalid_obb:751a558c-fe61-2c3b-8f4e-340ddb43b8bd:39:non_positive_aabb_extent`
- `invalid_obb:6a36053b-fa53-2915-9716-6b5361c7791a:32:non_positive_aabb_extent`
- `invalid_obb:ee527b51-0df9-2dae-829e-a0543a6e4074:13:non_positive_aabb_extent`
- `invalid_obb:95be45d7-a558-22da-9c39-ea7e57c68be5:4:non_positive_aabb_extent`
- `skipped_positive_counts:{'missing_subgraph_object': 6}`
- `selected_scans_without_positive_rows:['1c211552-f201-2d25-87ce-81e360c07b4a', '422885b1-192d-25fc-868c-110216f86479', '4a9a43d8-7736-2874-86fc-098deb94c868', 'bf9a3dbe-45a5-2e80-80ee-f78c2b525234', 'bf9a3dc3-45a5-2e80-832d-842aa34cc859']`

## Notes

- Use the declared scan split policy before fitting or reporting calibration metrics.
- Semantic scores remain null until the prediction adapter exists.
- Counterfactual negatives are high-margin synthetic candidates, not absent-edge negatives.

## Interpretation

Use the split policy in `24_calibration_data.md` before fitting any calibrator.

Next action: apply the split policy in `24_calibration_data.md` before fitting any calibrator.
