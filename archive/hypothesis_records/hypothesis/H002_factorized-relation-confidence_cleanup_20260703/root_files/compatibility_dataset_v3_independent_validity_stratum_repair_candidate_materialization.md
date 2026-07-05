# H002 Independent Validity Stratum Repair Candidate Materialization

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit
```

## Purpose

이 단계는 이전 plan에서 고정한 exact semantic-stratum quota를 실제 train-side
`match_rows.jsonl`에 적용해 repaired independent-validity candidate rows를 생성한다.

핵심 통제는 다음과 같다.

```text
predicate_label + subject_class_label + object_class_label
```

각 retained stratum 안에서 positive와 negative를 같은 수로 materialize했다. 따라서 이전
schema shortcut audit에서 문제가 됐던 `predicate_x_class_pair` shortcut을 다음 단계에서
직접 검증할 수 있다.

## Materialized Counts

```text
materialized_primary_rows = 1600
positive_rows = 800
negative_rows = 800
retained_exact_strata = 35
scan_cap_relaxation_rows = 0
```

Family counts:

| Family | Rows | Interpretation |
| --- | ---: | --- |
| `relative_vertical` | 1512 | primary exact-stratum repair slice |
| `support_contact_pose_conditioned` | 88 | diagnostic slice due limited exact-stratum capacity |

Predicate counts:

| Predicate | Rows |
| --- | ---: |
| `higher than` | 760 |
| `lower than` | 752 |
| `lying on` | 64 |
| `standing on` | 24 |

## Schema Precheck

All prechecks passed.

| Check | Result |
| --- | --- |
| row id unique | pass |
| train split only | pass |
| primary row count | `1600` |
| primary label balance | `800/800` |
| stratum internal balance | pass |
| retained exact strata | `35` |
| model-safe forbidden key hits | `0` |
| feature-block forbidden key hits | `0` |

The materialized `model_safe_view.jsonl` does not include construction summaries such as
`geometry_status`, `p_geom_valid`, `consistency_score`, or residual fields. These remain available
only in `candidate_rows.jsonl` / `hidden_manifest.jsonl` for audit.

## Artifacts

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization/
```

Key outputs:

- `candidate_rows.jsonl`
- `model_safe_view.jsonl`
- `smoke_ready_view.jsonl`
- `hidden_manifest.jsonl`
- `quota_audit.csv`
- `schema_precheck.json`
- `schema_precheck.csv`
- `materialization_manifest.json`
- `next_plan_contract.json`
- `validation_errors.jsonl`
- `report.md`

## Interpretation

이번 materialization은 H002의 기존 병목 중 하나였던 target shortcut 문제를 원리적으로
줄이기 위한 단계다. object-class semantics를 `T_e`에서 제거하지 않고, 대신 exact
predicate/object-class stratum 내부에서 label을 균형화했다.

따라서 다음 schema shortcut audit에서 `predicate_x_class_pair` probe가 낮아진다면,
기존 문제가 feature 설계 자체의 실패라기보다 target construction shortcut이었다는
해석이 가능하다. 반대로 여전히 높은 shortcut이 남으면, independent-validity target 자체가
다른 hidden construction shortcut을 포함하고 있다는 뜻이다.

## Caveat

이 target은 family-balanced target이 아니다. `support_contact_pose_conditioned`는
exact-stratum capacity가 작아 `88` rows만 포함되므로 diagnostic slice로만 해석한다.

## Boundary

- Train split only.
- No validation/test usage.
- No learned smoke or model training.
- No H001 artifact modification.
- Not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit
```
