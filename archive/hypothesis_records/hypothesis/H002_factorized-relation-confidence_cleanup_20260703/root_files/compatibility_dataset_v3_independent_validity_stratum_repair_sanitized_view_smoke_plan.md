# H002 Independent Validity Stratum Repair Sanitized View Smoke Plan

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_ready
rows = 1600
positive / negative = 800 / 800
validation_errors = 0
learned_smoke_executed = false
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner
```

## Purpose

이 단계는 learned smoke를 실행하기 전에, repaired independent-validity target에서 어떤
input view, baseline, control, gate를 비교할지 고정한다.

중요한 차이는 이전 same-G compatibility smoke와 달리, 이 target은 independent-validity
target이라는 점이다. 따라서 `G_e_raw` 자체가 예측력을 가질 수 있다. 이 경우
geometry-only 성능을 suppress하면 안 되고, 반드시 강한 baseline으로 보고해야 한다.

## Input

Source:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit/sanitized_primary_view.jsonl
```

Plan-local smoke input:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan/smoke_ready_view.jsonl
```

Counts:

```text
rows = 1600
positive = 800
negative = 800
groups = 1097
mixed_label_groups = 491
retained_exact_strata = 35
```

Family counts:

| Family | Rows | Interpretation |
| --- | ---: | --- |
| `relative_vertical` | 1512 | primary scope |
| `support_contact_pose_conditioned` | 88 | diagnostic-only slice |

## Planned Baselines

| Model | Input | Role |
| --- | --- | --- |
| `M0_intercept` | none | class-balance sanity baseline |
| `M1_semantic_only_T` | `T_e` | semantic shortcut baseline |
| `M2_source_only_Z` | `Z_e_safe` | source confidence shortcut baseline |
| `M3_semantic_source_TZ` | `T_e + Z_e_safe` | non-geometry shortcut baseline |
| `M4_geometry_only_G` | `G_e_raw` | geometry-only baseline |
| `M5_TG_concat` | `T_e + G_e_raw` | simple fusion baseline |
| `M6_TG_compatibility_interaction` | `T_e + G_e_raw` | primary `C_e` smoke |
| `M7_factorized_TZGQ` | `T_e + Z_e_safe + G_e_raw + Q_e_safe` | full factorized smoke |

## Planned Controls

- `shuffled_G_global`
- `shuffled_G_within_predicate`
- `wrong_predicate_family`
- `no_interaction_concat`

## Gates

```text
semantic/source shortcut AUROC <= 0.60
primary M6 or M7 AUROC >= 0.65
primary gain over semantic/source max >= 0.05
geometry dominance margin = 0.02
```

Interpretation rules:

- If semantic/source baselines are high, target shortcut remains.
- If geometry-only `M4` is almost equal to factorized `M6/M7`, then the result supports a
  geometry-evidence baseline rather than factorized compatibility novelty.
- If shuffled-G controls do not degrade, the method is not using aligned geometry.
- `support_contact_pose_conditioned` remains diagnostic because the slice has only `88` rows.

## Artifacts

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan/
```

Key outputs:

- `smoke_ready_view.jsonl`
- `input_manifest.json`
- `smoke_plan.json`
- `model_views.csv`
- `gates.csv`
- `controls.csv`
- `input_profile.csv`
- `feature_paths.csv`
- `summary.json`
- `validation_errors.jsonl`
- `report.md`

## Boundary

- Train-only smoke plan.
- No learned smoke executed.
- No validation/test usage.
- No H001 artifact modification.
- Not paper evidence.

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner
```
