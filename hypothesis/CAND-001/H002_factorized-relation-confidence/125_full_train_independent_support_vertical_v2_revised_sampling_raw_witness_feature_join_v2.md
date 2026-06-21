# Full-Train Independent Support/Vertical V2 Revised Sampling Raw-Witness Feature Join V2

## Purpose

`124_full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.md`
에서 결정한 대로, all-label-ready posterior rows에 `match_rows.geometry.raw_features`를
`prediction_id` 기준으로 join한다.

이 단계의 목적은 posterior 성능을 측정하는 것이 아니라, 다음 smoke가 사용할
typed raw-witness feature contract를 실제 row artifact로 만드는 것이다.

## Boundary

- Train-only feature-join step이다.
- Validation/test row는 사용하지 않았다.
- posterior model은 학습하지 않았다.
- review fields, target labels, hidden construction axes, packet paths, multi-view evidence,
  `geometry_status` shortcut은 model input이 아니다.
- 결과는 hypothesis-stage artifact이며 paper-level metric이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.py
```

Console summary:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_ready
rows=134
pos=67
neg=67
raw_matches=134/134
validation_errors=0
leakage=0
validation_used=False
next=revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke
```

## Result

Status:

```text
full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_ready
```

Target:

| Rows | Positive | Negative |
| ---: | ---: | ---: |
| 134 | 67 | 67 |

Family distribution:

| Family | Rows |
| --- | ---: |
| `support_contact` | 99 |
| `relative_vertical` | 35 |

Raw witness join:

| Item | Count |
| --- | ---: |
| requested prediction ids | 134 |
| matched prediction ids | 134 |
| match rows scanned until complete | 3,978,876 |
| raw fields | 14 |

Validation:

| Check | Count |
| --- | ---: |
| validation errors | 0 |
| feature leakage hits | 0 |

## Raw Witness Fields

```text
center_delta_z
distance_3d
distance_xy
normalized_center_delta_z
normalized_distance_3d
normalized_distance_xy
object_bottom_z
object_top_z
projected_iou_xy
projected_object_overlap_ratio
projected_subject_overlap_ratio
subject_bottom_z
subject_top_z
vertical_gap_subject_on_object
```

## Main Views

| View | Role |
| --- | --- |
| `semantic_only` | source semantic score/rank baseline. |
| `legacy_geometry_only` | old `p_geom_valid + consistency_score` geometry baseline. |
| `semantic_plus_geometry` | old reference baseline. |
| `raw_witness_only_v2` | typed raw witness only. |
| `semantic_plus_raw_witness_v2` | semantic evidence plus repaired raw witness evidence. |
| `factorized_reliability_posterior_v2_linear` | low-capacity repaired factorized posterior input. |
| `factorized_reliability_posterior_v2_family_shrinkage` | constrained family-local residual interaction input. |
| `endpoint_type_ablation` | endpoint type ablation only; not main claim input. |

## Control Views

| View | Role |
| --- | --- |
| `raw_witness_shuffle_global` | raw witness globally shuffled while semantic/legacy source evidence stays on the row. |
| `raw_witness_shuffle_within_family` | raw witness shuffled inside each relation family. |
| `wrong_pair_raw_witness` | raw witness replaced by another pair, preferring same scan when possible. |
| `family_only_offset` | deterministic family gates only. |
| `no_family_local_normalization` | v2 feature block without family-local z features. |
| `legacy_p_geom_only` | old p_geom-only diagnostic baseline. |

## Input Contract

Allowed model inputs:

- source semantic score/rank after label lock.
- legacy `p_geom_valid` as baseline/auxiliary scalar.
- raw geometry witness values keyed by `prediction_id`.
- deterministic typed witness gates.
- train-only family-local raw residual normalization.
- coverage/missingness indicators.
- endpoint type flags only in `endpoint_type_ablation`.

Forbidden model inputs:

- review fields.
- target labels.
- hidden audit metadata.
- packet paths.
- multi-view evidence.
- queue/role/rank-band construction axes.
- `geometry_status` satisfied/unsatisfied shortcut.
- free predicate/family categorical shortcut.
- validation/test rows.

## Interpretation

이 artifact는 H002의 핵심 전환을 실제 row schema로 만든다.

```text
legacy geometry scalar -> typed relation-specific raw witness evidence
```

따라서 다음 smoke에서는 `p_geom_valid`만 쓴 baseline과 raw witness v2를 분리해서 비교할 수 있다.
아직 posterior 성능 claim은 없다.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/input_contract_v2.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/posterior_ready_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/feature_ranges.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/family_local_stats.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/feature_leakage.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/validation_errors.jsonl
```

Line counts:

```text
posterior_ready_rows.jsonl = 134
feature_ranges.csv = 501 lines
family_local_stats.csv = 21 lines
feature_leakage.jsonl = 0
validation_errors.jsonl = 0
```

## Next TODO

```text
revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke
```

Goal:

- v2 views와 controls를 train-only grouped-by-scan smoke로 비교한다.
- `factorized_reliability_posterior_v2_family_shrinkage`가 `semantic_plus_geometry`를 이기는지 본다.
- raw witness shuffle controls가 v2 gain을 제거하는지 확인한다.
- 결과는 계속 hypothesis-stage diagnostic으로 제한한다.
