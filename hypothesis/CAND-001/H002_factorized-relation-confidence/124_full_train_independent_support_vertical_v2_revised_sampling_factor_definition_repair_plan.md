# Full-Train Independent Support/Vertical V2 Revised Sampling Factor Definition Repair Plan

## Purpose

`123_full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.md`
이후, H002의 다음 실패 원인을 `posterior combiner capacity`가 아니라
`factor/evidence definition` 문제로 보고 다음 feature contract를 고정한다.

핵심 질문:

```text
semantic score, p_geom_valid, consistency_score, disagreement만으로 relation
reliability를 설명하지 못한다면, 어떤 evidence factor를 먼저 고쳐야 하는가?
```

## Boundary

- Train-only hypothesis-stage repair plan이다.
- Validation/test row는 사용하지 않았다.
- 새 모델은 학습하지 않았다.
- 이 단계는 posterior combiner를 바꾸지 않고 input evidence contract를 바꾼다.
- review fields, target labels, hidden construction axes, packet paths, multi-view evidence는 model input이 아니다.
- 결과는 paper-level metric이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.py
```

Console summary:

```text
status=full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_ready
rows=134
validation_used=False
changes_feature_contract=True
changes_combiner=False
raw_fields=14
d_auprc_factorized_vs_sg=-0.0058
next=revised_sampling_all_label_ready_raw_witness_feature_join_v2
```

## Diagnosis Used

From controlled error analysis:

| Family | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 99 | 50 | 49 | +0.0023 | +0.0044 | +2 |
| `relative_vertical` | 35 | 17 | 18 | -0.0813 | +0.0100 | +2 |

Interpretation:

- `support_contact`는 factorized posterior가 ranking을 거의 보태지만 calibration을 해친다.
- `relative_vertical`은 factorized posterior가 `semantic_plus_geometry`의 기존 ranking signal을 크게 손상한다.
- `coverage`는 all-label-ready strict slice에서 거의 상수라서 현재 posterior 개선 요인이 아니다.
- `p_geom_valid >= 0.75` row가 대부분인데도 positive/negative가 섞여 있으므로, `p_geom_valid`는 relation reliability posterior의 main evidence로 충분하지 않다.

## Repair Decision

현재 실패는 다음처럼 해석한다.

```text
p_geom_valid is geometry-only evidence, not relation reliability.
```

따라서 `p_geom_valid`를 제거하지는 않는다. 대신 역할을 낮춘다.

- `p_geom_valid`: legacy geometry-only baseline 및 auxiliary scalar.
- raw witness residual: next main geometry evidence.
- predicate family: free categorical shortcut이 아니라 deterministic typed witness router.
- posterior combiner: raw witness v2 smoke 전까지 high-capacity model로 확장하지 않음.

## Factor Contracts

| Factor | Scope | Role |
| --- | --- | --- |
| `FD0_typed_relation_router` | all | predicate를 relation-specific witness template로 route한다. free family offset은 금지한다. |
| `FD1_support_contact_raw_witness` | `support_contact` | contact gap, xy support overlap, support distance를 분리한다. |
| `FD2_relative_vertical_order_witness` | `relative_vertical` | higher/lower를 signed vertical order와 margin으로 표현한다. |
| `FD3_family_local_normalization` | support/vertical | raw residual을 family 내부 scale로 normalize한다. |
| `FD4_uncertainty_and_boundary_evidence` | all | boundary/ambiguous geometry와 strong support/contradiction을 분리한다. |
| `FD5_optional_endpoint_type_ablation` | `support_contact` | floor/wall/room-surface endpoint type이 shortcut인지 ablation으로만 점검한다. |

## Raw Witness Contract

`match_rows.jsonl`에서 확인한 raw fields:

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

다음 feature join v2는 `prediction_id` 기준으로
`match_rows.geometry.raw_features`를 all-label-ready posterior rows에 join해야 한다.

금지:

- `geometry_status` satisfied/unsatisfied shortcut.
- `label_match_status`, `queue_kind`, `rank_band`, `proposed_audit_role`.
- review fields.
- target labels.
- packet path.
- multi-view feature.
- validation/test row.
- free predicate/family categorical shortcut.

허용:

- source semantic score/rank after label lock.
- raw geometry witness values.
- deterministic typed witness gates.
- coverage/missingness indicators.
- train-only family-local normalization statistics.

## Next Smoke Views

다음 smoke는 최소한 아래 비교군을 포함해야 한다.

| View | Purpose |
| --- | --- |
| `semantic_only` | 기존 semantic baseline. |
| `legacy_geometry_only` | 기존 `p_geom_valid + consistency_score` baseline. |
| `semantic_plus_geometry` | 현재 reference baseline. |
| `raw_witness_only_v2` | repaired geometry evidence 단독 신호 확인. |
| `semantic_plus_raw_witness_v2` | `semantic_plus_geometry`의 직접 대체 후보. |
| `factorized_reliability_posterior_v2_linear` | low-capacity repaired factorized posterior. |
| `factorized_reliability_posterior_v2_family_shrinkage` | family-local residual을 constrained shrinkage로 결합. |
| `endpoint_type_ablation` | endpoint type이 shortcut인지 확인하는 ablation-only view. |

필수 controls:

- `raw_witness_shuffle_global`
- `raw_witness_shuffle_within_family`
- `wrong_pair_raw_witness`
- `family_only_offset`
- `no_family_local_normalization`
- `legacy_p_geom_only`

## Success Gate

`factorized_reliability_posterior_v2_family_shrinkage`가 다음 조건을 만족해야만
combiner 확장을 논의할 수 있다.

```text
grouped_by_scan_delta_auprc_vs_semantic_plus_geometry >= +0.02
grouped_by_scan_delta_brier_vs_semantic_plus_geometry <= 0
new_errors_minus_fixes <= 0
support_contact: delta_brier <= 0 and delta_auprc >= 0
relative_vertical: delta_auprc >= 0 and no threshold regression
raw witness shuffle controls remove most of the v2 gain
```

## Decision

다음 단계는 combiner 교체가 아니라 raw-witness feature join v2다.
즉, H002는 그대로 relation-level reliability posterior 문제로 유지하되,
posterior에 들어가는 geometry evidence를 `p_geom_valid` scalar에서 typed raw witness
residual로 바꾼다.

Allowed claim:

```text
The current all-label-ready smoke identifies feature/family alignment as the
next blocker.
```

Blocked claim:

```text
The current factorized posterior improves relation reliability.
```

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/input_contract_v2.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/factor_contracts.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/feature_blocks.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/next_smoke_plan.json
```

## Next TODO

```text
revised_sampling_all_label_ready_raw_witness_feature_join_v2
```

Goal:

- all-label-ready posterior rows에 `match_rows.geometry.raw_features`를 `prediction_id` 기준으로 join한다.
- `FD1_support_contact_raw_witness`, `FD2_relative_vertical_order_witness`, `FD3_family_local_normalization`, `FD4_uncertainty_and_boundary_evidence`를 실제 `baseline_inputs`로 만든다.
- leakage check에서 review/target/hidden/packet/multi-view/geometry_status shortcut을 차단한다.
- 아직 posterior smoke를 확정 claim으로 쓰지 않는다.
