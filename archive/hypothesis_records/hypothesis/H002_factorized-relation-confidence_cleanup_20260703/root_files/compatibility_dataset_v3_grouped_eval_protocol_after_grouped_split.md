# H002 Grouped Evaluation Protocol After Grouped Split

## Status

```text
status = h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready
selected_path = grouped_eval_protocol_ready_select_grouped_eval_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_runner_after_protocol
```

## Purpose

이 단계는 grouped evaluation metric을 실행하기 전에 평가 계약을 고정한다.
이전 단계에서 `6952`개 row와 `3684`개 `cv_group_id` group을 내부
`internal_train`, `internal_dev`, `internal_heldout` split으로 나누었지만,
아직 어떤 model view를 어떤 feature로 학습/평가할지 고정하지 않았다.

따라서 이 문서는 다음을 잠근다.

- target: `C_e`
- train split: `internal_train`
- dev split: `internal_dev`
- heldout split: `internal_heldout`
- main `C_e` input: `T_e`, `G_e`
- blocked from main `C_e`: `Z_e`, `Q_e`, `extra_safe_blocks`
- official validation/test: 사용하지 않음
- paper-level metric: 생성하지 않음

## Input

```text
experiments/H002_compatibility_routing/splits/latest/model_safe_split_view.jsonl
experiments/H002_compatibility_routing/splits/latest/split_manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit/summary.json
```

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split.py
```

## Artifact Outputs

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/model_view_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/metric_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/blocked_feature_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/output_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/next_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/report.md
```

## Row Scope

| Route family | Rows | Label 0 | Label 1 | Train | Dev | Heldout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `relative_horizontal` | 2400 | 1200 | 1200 | 1680 | 360 | 360 |
| `relative_vertical` | 1512 | 756 | 756 | 1059 | 227 | 226 |
| `size_relative` | 2400 | 1200 | 1200 | 1680 | 360 | 360 |
| `support_contact` | 640 | 320 | 320 | 449 | 97 | 94 |

Total:

```text
rows = 6952
internal_train = 4868
internal_dev = 1044
internal_heldout = 1040
```

## Model Views

| View | Role | Allowed blocks | Use |
| --- | --- | --- | --- |
| `M0_constant` | sanity baseline | none | prior sanity only |
| `M1_T_semantic_only` | semantic-content baseline | `T_e` | predicate/object semantic baseline |
| `M2_G_geometry_only` | geometry-only baseline | `G_e` | predicate-independent geometry baseline |
| `M3_T_plus_G_concat` | naive fusion baseline | `T_e`, `G_e` | simple concat baseline |
| `M4_TxG_compatibility` | primary `C_e` model | `T_e`, `G_e` | predicate-geometry compatibility evidence |
| `C1_wrong_T_control` | counterfactual control | `T_e`, `G_e` | wrong semantic condition should degrade/invert |
| `C2_shuffled_G_control` | counterfactual control | `T_e`, `G_e` | shuffled geometry should degrade toward chance |
| `D1_Z_source_confidence_diagnostic` | diagnostic only | `Z_e` | source shortcut check, not main `C_e` |
| `D2_Q_observability_diagnostic` | diagnostic only | `Q_e` | future `p_obs` check, not main `C_e` |

## Metrics

Required metrics:

- `AUROC`
- `AUPRC`
- `balanced_accuracy`
- `macro_F1`
- `Brier`
- `NLL_if_probabilistic`

Required breakdowns:

- overall macro over route families
- per route family
- per predicate
- `internal_dev`
- `internal_heldout`

Primary comparison:

```text
M4_TxG_compatibility
vs
M1_T_semantic_only, M2_G_geometry_only, M3_T_plus_G_concat
```

Required controls:

```text
M4_TxG_compatibility vs C1_wrong_T_control
M4_TxG_compatibility vs C2_shuffled_G_control
```

## Blocked Features

The grouped evaluation runner must not use:

- `cv_group_id`
- `unified_row_id`
- `source_row_id`
- `source_artifact`
- `model_safe_source`
- `protocol_split`
- `split_policy`
- `feature_use_policy`
- `paper_metric_ready`
- `route_role`
- hidden manifest fields
- construction fields such as `construction_bucket`, `label_match_status`,
  `geometry_status`, `candidate_bucket`, `distance_bucket`
- `feature_blocks.Z_e` in main `C_e`
- `feature_blocks.Q_e` in main `C_e`
- `feature_blocks.extra_safe_blocks` in main `C_e`

`Z_e` and `Q_e` can only appear as diagnostic-only views until a later protocol
explicitly enables `p_rel` or `p_obs`.

## Next Runtime Output Contract

The next runner should write:

```text
experiments/H002_compatibility_routing/evaluation/latest/eval_manifest.json
experiments/H002_compatibility_routing/evaluation/latest/model_view_manifest.json
experiments/H002_compatibility_routing/evaluation/latest/route_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/predicate_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/control_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/prediction_scores.jsonl
experiments/H002_compatibility_routing/evaluation/latest/leakage_audit.csv
experiments/H002_compatibility_routing/evaluation/latest/validation_errors.jsonl
```

## Boundary

- Protocol only.
- Grouped metric has not been run.
- Official validation/test has not been used.
- Paper metric has not been produced.
- `p_obs` / `p_rel` claims are not enabled by this protocol.
- This protocol evaluates `C_e` compatibility only.

## Next

```text
compatibility_dataset_v3_grouped_eval_runner_after_protocol
```

The next step is to implement the grouped evaluation runner or Docker service
following this protocol.
