# Source Reranking Docker Materialization

## Status

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_materialization/latest/
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol/
status = h002_source_reranking_docker_materialization_after_protocol_ready
selected_path = source_reranking_docker_materialized_select_schema_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization
```

## Purpose

이 단계는 source reranking protocol에서 막혀 있던 `S2_source_x_Ce` 계산 준비를 위해,
`VL-SAT`와 `Open3DSG` official validation source prediction universe 전체에 대해 H002
model-safe materialization view를 실제로 생성한 Docker 실행 단계다.

Metric을 실행하지 않았다. Official test도 사용하지 않았다. Paper metric promotion도 없다.

## Result

Docker service:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-materialize
```

Generated runtime outputs:

| Output | Rows | Role |
| --- | ---: | --- |
| `source_candidates.jsonl` | 762888 | source prediction identity rows |
| `model_safe_ce_view.jsonl` | 762888 | `C_e` input, `T_e + G_e` only |
| `model_safe_geometry_only_view.jsonl` | 762888 | `G_e` diagnostic/control input |
| `source_rank_view.jsonl` | 762888 | `Z_e` source score/rank for reranking only |
| `hidden_metric_manifest.jsonl` | 762888 | GT match and violation labels for metric only |
| `validation_errors.jsonl` | 0 | runtime validation errors |

Family counts:

| Family | Rows | Role |
| --- | ---: | --- |
| `relative_vertical` | 127148 | primary success family |
| `size_relative` | 127148 | primary success family |
| `relative_horizontal` | 254296 | caveated frame-aware family |
| `proximity` | 63574 | geometry-only control |
| `support_contact` | 190722 | diagnostic/failure taxonomy |

Source counts:

| Source | Rows |
| --- | ---: |
| `vlsat_full_validation` | 441696 |
| `open3dsg_recovery_relaxed_views_min2` | 321192 |

## Boundary

- `model_safe_ce_view.jsonl` contains only `T_e` and `G_e` feature blocks.
- `source_rank_view.jsonl` owns `Z_e`; it is reranking-only and not part of `C_e`.
- `hidden_metric_manifest.jsonl` owns GT and violation labels; it is metric-only.
- `support_contact` remains excluded from success aggregation.
- No `Recall@K`, `Violation@K`, source reranking metric, official test, or paper result was produced.

## Next Step

다음 TODO는 `compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization`다.
이 단계에서 blocked field deep scan, hidden/source-score separation, family-balanced
success aggregation, and control-generation readiness를 더 엄격히 확인해야 한다.
