# H002 Grouped Eval Feature Extractor Repair

## Status

```text
status = h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_ready
selected_path = feature_extractor_repair_ready_select_claim_boundary_review
validation_errors = 0
next_todo = compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

## Purpose

`relative_vertical` failure analysis에서 확인된 grouped eval runner의 feature
extraction 문제를 수정했다. 기존 runner는 `center_delta_z`를 suffix 기반으로 찾다가
`raw_geometry_feature_available_mask.center_delta_z=True`를 먼저 읽었다. 이 때문에
`T_e x G_e` compatibility feature에 실제 z difference가 들어가지 않았다.

## Repair

`experiments/H002_compatibility_routing/scripts/run_grouped_eval.py`에서
`compatibility_features()`가 relation-specific geometry를 explicit raw feature path로
읽도록 수정했다.

예:

```text
center_delta_z -> G_e_raw.raw_geometry_feature_vector.center_delta_z
normalized_center_delta_z -> G_e_raw.raw_geometry_feature_vector.normalized_center_delta_z
log_volume_ratio_s_over_o -> G_e_size.log_volume_ratio_s_over_o
delta_x_subject_minus_object -> G_e_horizontal.delta_x_subject_minus_object
surface_gap_subject_bottom_to_object_top -> G_e_obb_baseline.surface_gap_subject_bottom_to_object_top
point_surface_gap_subject_bottom_to_object_top -> G_e_contact_patch.point_surface_gap_subject_bottom_to_object_top
```

Repair probe:

```text
raw_center_delta_z = 0.331904970141389
repaired_numeric_center_delta_z = 0.331904970141389
matches_raw_center_delta_z = true
```

## Commands

```bash
python -m py_compile experiments/H002_compatibility_routing/scripts/run_grouped_eval.py
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-eval
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_grouped_eval_runner_after_protocol.py
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_grouped_eval_result_review_after_runner.py
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis.py
```

## Repaired Internal Heldout

| Family | Status | Heldout M4 AUROC | Balanced acc | Delta vs M1 | Delta vs M2 | Delta vs M3 | Delta vs wrong-T | Delta vs shuffled-G |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `relative_horizontal` | claim-supporting | 0.969568 | 0.908333 | 0.513796 | 0.469568 | 0.513796 | 0.939136 | 0.429660 |
| `relative_vertical` | claim-supporting | 0.999921 | 0.995192 | 0.568135 | 0.519861 | 0.541929 | 0.999921 | 0.520334 |
| `size_relative` | claim-supporting | 0.999969 | 0.994444 | 0.483302 | 0.499969 | 0.483302 | 0.999938 | 0.534491 |
| `support_contact` | partial | 0.610960 | 0.551630 | 0.177763 | 0.121150 | 0.178895 | 0.235960 | 0.152627 |

Overall heldout:

| View | AUROC |
| --- | ---: |
| `M1_T_semantic_only` | 0.454321 |
| `M2_G_geometry_only` | 0.487690 |
| `M3_T_plus_G_concat` | 0.465868 |
| `M4_TxG_compatibility` | 0.984976 |
| `C1_wrong_T_control` | 0.014425 |
| `C2_shuffled_G_control` | 0.493975 |

## Interpretation

- `relative_vertical` is restored as claim-supporting evidence after repair.
- `relative_horizontal`, `relative_vertical`, and `size_relative` are now strong
  internal compatibility-route evidence.
- `support_contact` remains partial/challenging and should not be described as solved.
- This is still internal H002 candidate-pool evidence, not official validation/test or
  paper-level evidence.

## Boundary

- official validation/test 사용 없음.
- paper-level metric 생성 없음.
- `p_obs` / `p_rel` claim 생성 없음.
- `Z_e` / `Q_e`는 main `C_e`에 사용하지 않음.
- H001 artifact 수정 없음.

## Next

```text
compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

다음 단계에서는 repaired grouped result를 기준으로 최종 H002 claim boundary를
다시 정리해야 한다.
