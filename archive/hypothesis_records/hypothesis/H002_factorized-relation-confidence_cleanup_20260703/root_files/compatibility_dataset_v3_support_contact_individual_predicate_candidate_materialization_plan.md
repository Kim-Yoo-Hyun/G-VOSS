# H002 Support/Contact Individual Predicate Candidate Materialization Plan

작성일: 2026-06-29 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_ready
selected_path = materialize_route_aware_standing_lying_candidates_with_supported_by_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization
```

## 핵심 결정

이번 단계는 실제 row를 아직 뽑지 않고, relation별 evidence route와 materialization
quota를 고정하는 plan 단계다.

- `standing on`: main compatibility-ready target으로 materialize한다.
- `lying on`: secondary compatibility-ready target으로 materialize한다.
- `supported by`: superordinate relation이므로 main binary target에서 제외하고 diagnostic으로만 유지한다.

즉, grouped support/contact를 하나의 relation으로 섞지 않고, relation type별로 필요한
evidence route가 다르다는 현재 H002 방향을 반영한다.

## Planned Quota

| Subset | Predicate | Role | Target | Rows |
| --- | --- | --- | --- | ---: |
| main compatibility | `standing on` | clear accept | `C_e = 1` | 160 |
| main compatibility | `standing on` | lying-like hard reject | `C_e = 0` | 160 |
| main compatibility | `lying on` | clear accept | `C_e = 1` | 160 |
| main compatibility | `lying on` | standing-like hard reject | `C_e = 0` | 160 |
| diagnostic | `supported by` | clear accept | diagnostic accept | 40 |
| diagnostic | `supported by` | no-support hard reject | diagnostic reject | 40 |
| diagnostic | `supported by` | overlap/abstain | diagnostic abstain | 80 |

Total planned rows:

```text
main compatibility rows = 640
supported-by diagnostic rows = 160
total rows = 800
```

## Gates

All materialization plan gates passed.

```text
standing_class_pair_capacity = 382 / 320
lying_class_pair_capacity = 414 / 320
supported_by_diagnostic_capacity = 164 / 80
planned_total_rows = 800 / 800
supported_by_not_main_target = diagnostic_only
```

## Sampling Caps

```text
max_rows_per_scan = 20
max_rows_per_predicate_class_pair = 32
max_rows_per_predicate_class_pair_rank = 24
max_rows_per_directed_pair = 2
max_hard_surface_rows = 360
```

## Model/Input Boundary

The next materialization must create both model-safe rows and a hidden manifest.

Model-safe views may include controlled `T_e`, `G_e`, `Q_e`, and route-specific
feature views. The following fields must remain blocked from model inputs and
used only for audit/control:

- `label_match_status`
- `geometry_status`
- `candidate_role`
- `rank_band`
- `semantic_rank`
- source score fields for `C_e`
- `p_geom_valid`
- old H001 geometry verification status
- scan/object identity fields
- hidden construction fields

## Interpretation

This result supports the current H002 process:

1. define relation-specific evidence routes first;
2. use compatibility-ready relations as main learned targets;
3. keep superordinate or ambiguous relations as diagnostic/control evidence;
4. only after materialization and shortcut audit decide whether learned smoke is valid.

`standing on` and `lying on` are now ready for actual candidate materialization.
`supported by` remains useful for taxonomy and `Q_e`/abstain diagnostics, but not as a
clean main binary compatibility target.

