# H002 Independent Validity Stratum Repair Materialization Plan

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_ready
selected_path = materialize_exact_predicate_class_balanced_independent_validity_rows
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization
```

## Purpose

이 단계의 목적은 이전 independent-validity target에서 발생한 가장 강한 shortcut을
정면으로 통제하는 것이다. 이전 4027-row artifact는 전체 label balance는 맞았지만,
`predicate_label + subject_class_label + object_class_label`만으로 label을 거의 맞출 수
있었다.

따라서 다음 materialization은 exact semantic stratum 내부에서 positive/negative를
1:1로 뽑도록 고정한다.

```text
stratum = predicate_label + subject_class_label + object_class_label
```

## Planned Counts

```text
target_primary_rows = 1600
planned_primary_rows = 1600
planned_positive_rows = 800
planned_negative_rows = 800
retained_exact_strata = 35
max_pairs_per_stratum = 125
```

Family distribution:

| Family | Planned Rows | Interpretation |
| --- | ---: | --- |
| `relative_vertical` | 1512 | primary exact-stratum repair slice |
| `support_contact_pose_conditioned` | 88 | diagnostic slice due limited exact-stratum capacity |

Predicate distribution:

| Predicate | Planned Rows |
| --- | ---: |
| `higher than` | 760 |
| `lower than` | 752 |
| `lying on` | 64 |
| `standing on` | 24 |

## Quota Policy

- exact predicate-class stratum 안에 positive와 negative가 모두 있는 strata만 사용한다.
- retained stratum마다 positive/negative quota를 동일하게 둔다.
- single stratum dominance를 막기 위해 stratum당 최대 `125` positive/negative pair로 제한한다.
- support/contact exact mixed capacity는 매우 작으므로 가능한 scan-capped capacity를 먼저 모두 포함한다.
- 남은 quota는 relative-vertical exact mixed strata로 채운다.
- no-GT, geometry-uncertain, GT-conflict row는 이 primary repaired target에서는 보류한다.

## Important Caveat

이 target은 family-balanced generality target이 아니다. Full train에서는 exact
predicate-class repair 자체는 가능하지만, exact stratum 내부 mixed capacity가
`relative_vertical`에 크게 몰려 있다. 따라서 다음 materialization이 통과하더라도 claim은
다음처럼 제한해야 한다.

```text
independent-validity shortcut repair is feasible and testable,
most strongly for relative_vertical;
support/contact is retained as a capacity-limited diagnostic stress slice.
```

이 caveat를 숨기면 H002의 현재 방향을 과장하게 된다.

## Blocked Model Inputs

다음 필드는 다음 materialized model view에서 금지한다.

- `geometry_status`
- `p_geom_valid`
- `consistency_score`
- `geometry_residual_proxy`
- `geometry_axis`
- `label_match_status`
- matched GT provenance
- scan/object/prediction ids
- target pool and selection metadata

사용 가능한 geometry input은 construction summary가 아니라 raw metric geometry evidence여야 한다.

```text
G_e_raw = raw distance, height, overlap, contact/gap, object size,
          pair pose, and availability mask features
```

## Artifacts

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan/
```

Key files:

- `summary.json`
- `stratum_quota_plan.csv`
- `row_schema_contract.json`
- `matching_policy.json`
- `blocked_field_table.csv`
- `next_plan_contract.json`
- `warnings.jsonl`
- `validation_errors.jsonl`
- `report.md`

## Boundary

- Train-only materialization plan.
- No validation/test usage.
- No row materialization in this stage.
- No learned smoke or model training.
- No H001 artifact modification.
- Not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization
```
