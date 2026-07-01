# H002 Grouped Evaluation Runner After Protocol

## Status

```text
status = h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready
selected_path = grouped_eval_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_grouped_eval_result_review_after_runner
```

## Purpose

Locked grouped evaluation protocol에 따라 내부 H002 candidate-pool split에서
`C_e` compatibility model views를 실행했다.

이 단계는 metric을 생성하지만, 아직 paper-level result가 아니다. 이유는 다음과
같다.

- official validation/test가 아니다.
- H002 candidate pool 내부 heldout이다.
- result-review와 claim-lock을 아직 통과하지 않았다.
- `p_obs` / `p_rel` calibration을 평가하지 않았다.

## Command

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-eval
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_grouped_eval_runner_after_protocol.py
```

## Runtime Outputs

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

## Validation

```text
total rows = 6952
internal_train = 4868
internal_dev = 1044
internal_heldout = 1040
prediction_rows = 2084
validation_errors = 0
```

Leakage audit:

| Check | Status | Violations |
| --- | --- | ---: |
| `cv_group_single_split` | pass | 0 |
| `official_validation_test_usage` | pass | 0 |
| `blocked_C_e_blocks_not_used_in_main` | pass | 0 |

## Internal Heldout Overall

| View | AUROC | Balanced acc | Macro-F1 |
| --- | ---: | ---: | ---: |
| `M0_constant` | 0.500000 | 0.500000 | 0.329032 |
| `M1_T_semantic_only` | 0.454321 | 0.473511 | 0.472981 |
| `M2_G_geometry_only` | 0.487690 | 0.487514 | 0.439911 |
| `M3_T_plus_G_concat` | 0.465868 | 0.487921 | 0.487420 |
| `M4_TxG_compatibility` | 0.984976 | 0.924824 | 0.924946 |
| `C1_wrong_T_control` | 0.014425 | 0.073067 | 0.073073 |
| `C2_shuffled_G_control` | 0.493975 | 0.496300 | 0.496152 |
| `D1_Z_source_confidence_diagnostic` | 0.529288 | 0.509952 | 0.429506 |
| `D2_Q_observability_diagnostic` | 0.479606 | 0.482612 | 0.462025 |

## Internal Heldout M4 By Family

| Route family | Rows | AUROC | Balanced acc | Macro-F1 | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| `relative_horizontal` | 360 | 0.969568 | 0.908333 | 0.908333 | strong |
| `relative_vertical` | 226 | 0.999921 | 0.995192 | 0.995544 | repaired / strong |
| `size_relative` | 360 | 0.999969 | 0.994444 | 0.994444 | strong |
| `support_contact` | 94 | 0.610960 | 0.551630 | 0.549932 | partial / challenging |

## Internal Heldout Controls

| Comparison | Delta AUROC | Primary | Baseline |
| --- | ---: | ---: | ---: |
| `M4_vs_M1` | 0.530655 | 0.984976 | 0.454321 |
| `M4_vs_M2` | 0.497286 | 0.984976 | 0.487690 |
| `M4_vs_M3` | 0.519108 | 0.984976 | 0.465868 |
| `M4_vs_wrong_T` | 0.970551 | 0.984976 | 0.014425 |
| `M4_vs_shuffled_G` | 0.491001 | 0.984976 | 0.493975 |

## Immediate Interpretation

The grouped runner supports the aggregate `T_e x G_e` compatibility mechanism:
`M4_TxG_compatibility` is much stronger than `T_e`-only, `G_e`-only, plain
concat, wrong-`T_e`, and shuffled-`G_e` controls on the internal heldout split.

However, route-family review is mandatory before claim promotion:

- `size_relative`, `relative_vertical`, and `relative_horizontal` are strong after the feature extractor repair.
- `support_contact` is only partial.

Therefore, the next step is still result review and claim-boundary review, not paper-level claim promotion.

## Boundary

- This is internal H002 candidate-pool evidence.
- This is not official validation/test.
- This is not paper-level metric evidence yet.
- This does not enable `p_obs` or `p_rel` calibration claims.
- This does not prove all relation families are solved.

## Next

```text
compatibility_dataset_v3_grouped_eval_result_review_after_runner
```

The next stage must decide claim boundaries for the repaired grouped result,
especially how to report `support_contact` as partial/challenging.
