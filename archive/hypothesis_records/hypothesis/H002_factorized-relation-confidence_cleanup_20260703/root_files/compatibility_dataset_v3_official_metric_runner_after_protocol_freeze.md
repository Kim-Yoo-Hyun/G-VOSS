# Compatibility Dataset V3 Official Metric Runner After Protocol Freeze

## Status

```text
runtime_root = experiments/H002_compatibility_routing/official_evaluation/latest/
artifact_root = artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
status = h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_ready_with_caveats
selected_path = official_metric_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_official_metric_result_review_after_runner
```

## Purpose

Frozen protocol에 따라 official validation `C_e` metric runner를 Docker에서 실행했다.
이 단계는 official validation metric을 생성하지만, 아직 paper-level result promotion은 아니다.

Important boundary:

- official validation rows are eval-only.
- trainable views are fit on internal train only.
- official test was not used.
- main `C_e` uses only `T_e` and `G_e`.
- `Z_e`, `Q_e`, H001 `p_geom_valid`, and hidden fields are excluded from main `C_e`.
- `p_rel` / `p_obs` remain disabled.

## Docker Command

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-metric-runner
```

## Runtime Outputs

```text
experiments/H002_compatibility_routing/official_evaluation/latest/eval_manifest.json
experiments/H002_compatibility_routing/official_evaluation/latest/model_view_manifest.json
experiments/H002_compatibility_routing/official_evaluation/latest/family_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/predicate_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/aggregate_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/control_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/prediction_scores.jsonl
experiments/H002_compatibility_routing/official_evaluation/latest/leakage_audit.csv
experiments/H002_compatibility_routing/official_evaluation/latest/validation_errors.jsonl
```

## Main Snapshot

| View | Macro-family AUROC | Weighted-family AUROC | Overall AUROC |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.417633 | 0.455374 | 0.404333 |
| `M2_G_geometry_only` | 0.500000 | 0.500000 | 0.528329 |
| `M3_T_plus_G_concat` | 0.416923 | 0.454625 | 0.406137 |
| `M4_TxG_compatibility` | 0.835547 | 0.720781 | 0.724835 |

## M4 Family Metrics

| Family | AUROC | Balanced accuracy | Role |
| --- | ---: | ---: | --- |
| `relative_horizontal` | 0.719568 | 0.701522 | primary, needs frame-control review |
| `relative_vertical` | 0.991321 | 0.957692 | primary |
| `size_relative` | 0.999585 | 0.988235 | primary |
| `support_contact` | 0.631712 | 0.566394 | challenging/diagnostic, not solved |

## Control Snapshot

| Comparison | Delta AUROC | Interpretation |
| --- | ---: | --- |
| `M4_vs_M1` | 0.417913 | passes primary delta |
| `M4_vs_M2` | 0.335547 | passes primary delta |
| `M4_vs_M3` | 0.418624 | passes primary delta |
| `M4_vs_wrong_T_within_route` | 0.671120 | control degrades |
| `M4_vs_wrong_T_across_route` | 0.270464 | control degrades |
| `M4_vs_shuffled_G_global` | 0.341733 | control degrades |
| `M4_vs_shuffled_G_within_family` | 0.318753 | control degrades |
| `M4_vs_subject_object_swap` | 0.717045 | control degrades |
| `M4_vs_sign_flip` | 0.717045 | control degrades |
| `M4_vs_horizontal_frame_swap` | 0.038149 | weak control margin |

## Caveats

- `support_contact` remains challenging/diagnostic because M4 AUROC is `0.631712`
  and earlier schema audit found strong predicate/class-pair shortcut risk.
- `relative_horizontal` needs result review because `horizontal_frame_swap` control
  has weak margin: delta AUROC `0.038149`.
- This result should not be promoted to paper table until result review and claim
  boundary pass.

## Next

```text
compatibility_dataset_v3_official_metric_result_review_after_runner
```
