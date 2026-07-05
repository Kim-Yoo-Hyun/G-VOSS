# H002 Grouped Split Protocol After Materialization Schema Audit

## Status

```text
status = h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_ready
selected_path = grouped_split_ready_select_grouped_eval_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split
```

## Purpose

이 단계의 목적은 `6952`개 H002 materialized candidate row를 official
validation/test로 오해하지 않도록, 내부 candidate-pool 기준의 grouped split으로
나누는 것이다.

Split 기준은 `cv_group_id`다. 같은 counterfactual / same-geometry group이
`internal_train`, `internal_dev`, `internal_heldout`에 동시에 들어가면
compatibility metric이 row leakage를 통해 과대평가될 수 있으므로, 모든
`cv_group_id`는 정확히 하나의 split에만 배정한다.

## Command

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-split
```

Stage validator:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit.py
```

## Runtime Outputs

```text
experiments/H002_compatibility_routing/splits/latest/model_safe_split_view.jsonl
experiments/H002_compatibility_routing/splits/latest/split_assignments.jsonl
experiments/H002_compatibility_routing/splits/latest/group_manifest.jsonl
experiments/H002_compatibility_routing/splits/latest/split_manifest.json
experiments/H002_compatibility_routing/splits/latest/route_split_counts.csv
experiments/H002_compatibility_routing/splits/latest/predicate_split_counts.csv
experiments/H002_compatibility_routing/splits/latest/leakage_audit.csv
experiments/H002_compatibility_routing/splits/latest/validation_errors.jsonl
```

Hypothesis-stage summary artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit/
```

## Split Summary

Input rows:

```text
input_model_safe_rows = 6952
model_safe_split_view = 6952
split_assignments = 3684
group_manifest = 3684
validation_errors = 0
```

Target split ratios:

```text
internal_train = 0.70
internal_dev = 0.15
internal_heldout = 0.15
```

Observed route-family split:

| Route family | Split | Rows | Label 0 | Label 1 | CV groups |
| --- | --- | ---: | ---: | ---: | ---: |
| `relative_horizontal` | `internal_train` | 1680 | 840 | 840 | 840 |
| `relative_horizontal` | `internal_dev` | 360 | 180 | 180 | 180 |
| `relative_horizontal` | `internal_heldout` | 360 | 180 | 180 | 180 |
| `relative_vertical` | `internal_train` | 1059 | 519 | 540 | 717 |
| `relative_vertical` | `internal_dev` | 227 | 115 | 112 | 153 |
| `relative_vertical` | `internal_heldout` | 226 | 122 | 104 | 156 |
| `size_relative` | `internal_train` | 1680 | 840 | 840 | 840 |
| `size_relative` | `internal_dev` | 360 | 180 | 180 | 180 |
| `size_relative` | `internal_heldout` | 360 | 180 | 180 | 180 |
| `support_contact` | `internal_train` | 449 | 223 | 226 | 182 |
| `support_contact` | `internal_dev` | 97 | 49 | 48 | 44 |
| `support_contact` | `internal_heldout` | 94 | 48 | 46 | 32 |

## Leakage Audit

| Check | Status | Violations |
| --- | --- | ---: |
| `cv_group_single_split` | pass | 0 |
| `official_validation_test_usage` | pass | 0 |

추가로 validator는 `model_safe_split_view.jsonl`에서 모든 `cv_group_id`가 하나의
split에만 존재하는지 다시 확인했다.

## Boundary

- 이 split은 H002 candidate pool 내부 split이다.
- official validation/test는 사용하지 않았다.
- grouped heldout metric은 아직 실행하지 않았다.
- paper-level H002 metric은 아직 없다.
- `cv_group_id`, source artifact id, hidden construction field는 model feature로
  쓰면 안 된다.
- 다음 grouped evaluation도 `internal_dev` / `internal_heldout` metric으로만
  표현해야 한다.

## Next

```text
compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split
```

다음 단계에서는 metric을 바로 paper claim으로 승격하지 말고, 먼저 grouped
evaluation protocol을 명시해야 한다. 최소 비교군은 다음이다.

- semantic-only
- geometry-only
- `T_e + G_e` concat
- `T_e x G_e` compatibility
- wrong-`T_e` control
- shuffled-`G_e` control

`Q_e`와 `Z_e`는 `C_e` 평가에 바로 섞지 않는다. `Q_e`는 later selective /
abstention protocol에서, `Z_e`는 source-confidence baseline 또는 final
reliability head에서 별도 평가한다.
