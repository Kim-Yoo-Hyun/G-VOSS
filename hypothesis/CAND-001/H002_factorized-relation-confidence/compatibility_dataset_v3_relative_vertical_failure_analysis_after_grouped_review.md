# H002 Relative-Vertical Failure Analysis After Grouped Review

## Status

```text
status = h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_ready
selected_path = repair_grouped_eval_compatibility_feature_extractor_then_rerun
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis
```

## Purpose

Grouped evaluation에서 `relative_vertical`이 failed로 판정된 이유가 relation
family 자체의 한계인지, target 문제인지, split 문제인지, runner implementation
문제인지 분리했다.

## Outputs

```text
artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/summary.json
artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/feature_probe.csv
artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/feature_collision_audit.csv
artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/report.md
artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/validation_errors.jsonl
```

## Verdict

`relative_vertical` 실패는 relation family 자체가 안 된다는 증거가 아니라,
grouped runner의 compatibility feature extraction 문제로 보는 것이 맞다.

핵심 수치:

| Probe | Internal heldout AUROC |
| --- | ---: |
| intended `predicate_sign * raw_geometry_feature_vector.center_delta_z` | 1.000000 |
| runner suffix-based `center_delta_z` candidate | 0.504808 |
| reported grouped `M4_TxG_compatibility` | 0.457834 |

문제는 `numeric_value(..., "center_delta_z")`가 실제 raw z difference가 아니라
availability mask를 먼저 잡는다는 점이다.

| Suffix | Expected raw key | Runner selected key |
| --- | --- | --- |
| `center_delta_z` | `G.G_e_raw.raw_geometry_feature_vector.center_delta_z` | `G.G_e_raw.raw_geometry_feature_available_mask.center_delta_z` |
| `normalized_center_delta_z` | `G.G_e_raw.raw_geometry_feature_vector.normalized_center_delta_z` | `G.G_e_raw.raw_geometry_feature_available_mask.normalized_center_delta_z` |

결과적으로 `C.sign_x_center_delta_z`가 `predicate_sign * actual_z_delta`가 아니라
사실상 `predicate_sign * 1.0`이 되어, vertical relation에 필요한 geometry signal이
compatibility head에 들어가지 않았다.

## Interpretation

- Target은 의도한 signed vertical geometry로 train/dev/heldout 모두에서 분리된다.
- Split composition 문제로 보기 어렵다.
- `relative_vertical`을 main claim에서 제거할 단계가 아니다.
- 현재 grouped `M4` 실패는 scientific negative result가 아니라 runner feature
  extraction repair-needed 상태다.
- `M3_T_plus_G_concat`이 못 푸는 것은 자연스럽다. `higher than`과 `lower than`은
  predicate에 따라 같은 z difference를 반대로 해석해야 하므로 `T_e x G_e`
  interaction이 필요하다.

## Boundary

- official validation/test 사용 없음.
- paper-level metric 생성 없음.
- `p_obs` / `p_rel` claim 생성 없음.
- H001 artifact 수정 없음.

## Next

```text
compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis
```

다음 단계에서는 grouped runner가 suffix match가 아니라 explicit raw geometry path를
사용하도록 수정한 뒤 grouped evaluation을 다시 실행해야 한다.
