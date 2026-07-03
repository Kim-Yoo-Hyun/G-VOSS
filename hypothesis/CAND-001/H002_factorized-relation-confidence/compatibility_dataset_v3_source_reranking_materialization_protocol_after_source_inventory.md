# Source Reranking Materialization Protocol

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory/
status = h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_ready
selected_path = source_reranking_materialization_protocol_ready_select_docker_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol
```

## Purpose

Source reranking inventory에서 `VL-SAT`과 `Open3DSG` official validation source rows는
join key, source score, rank를 갖고 있음이 확인됐다. 그러나 현재 H002 `C_e` score는
official GT/counterfactual rows에만 존재하므로, source prediction universe 전체에
`S2_source_x_Ce`를 계산할 수 없다.

이 단계의 목적은 source reranking metric을 실행하기 전에 source-wide `C_e`
materialization protocol을 고정하는 것이다. 즉, 전체 source prediction rows에 대해
model-safe `T_e/G_e` view를 만들고, source score/rank와 hidden GT/violation label을
분리하는 Docker 구현 계약을 확정한다.

## Result

이번 단계에서는 metric을 실행하지 않았다. Official test도 사용하지 않았고, paper metric도
promote하지 않았다.

Planned runtime:

```text
runtime_output_dir = experiments/H002_compatibility_routing/source_reranking_materialization/latest
total_source_family_rows_to_materialize = 762888
primary_success_family_rows = 254296
```

Required outputs:

| Artifact | Role |
| --- | --- |
| `source_candidates.jsonl` | full source prediction universe with row identity |
| `model_safe_ce_view.jsonl` | `C_e` scoring input; `T_e + G_e` only |
| `model_safe_geometry_only_view.jsonl` | `G_e` diagnostic/control input |
| `source_rank_view.jsonl` | `Z_e` source score/rank for reranking stage only |
| `hidden_metric_manifest.jsonl` | GT match and violation labels for metric computation only |
| `row_manifest.json` | row counts, family counts, provenance, and policy flags |
| `validation_errors.jsonl` | runtime materialization validation errors |

## Schema Contract

`model_safe_ce_view.jsonl` may contain row identity fields for join/grouping, `T_e`, and
predicate-independent `G_e`. It must not contain source score, source rank, H001
`p_geom_valid`, GT match, violation status, construction label, or metric target fields.

`source_rank_view.jsonl` owns `Z_e`: source ranking score, predicate score, predicate rank,
semantic rank, and source id. `Z_e` is allowed only in the reranking stage, not inside
`C_e = compatibility(T_e, G_e)`.

`hidden_metric_manifest.jsonl` owns GT and violation labels. It is metric-only and must not be
used by the model-safe scorer.

## Next Step

다음 TODO는 `compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol`이다.
이 단계에서 Docker materializer를 구현/실행하고, 위 output들이 실제로 생성됐는지 검증해야 한다.
