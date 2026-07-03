# Source Reranking Source Inventory After Protocol Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan/
status = h002_compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan_ready
selected_path = source_inventory_ready_select_source_candidate_materialization_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory
```

## 목적

Source reranking protocol 이후, VL-SAT/Open3DSG source candidates가 실제 reranking
experiment에 필요한 조건을 갖췄는지 점검했다. 확인 항목은 source prediction join key,
source score/rank, GT match, H001 geometry verification, H002 `G_e`/`C_e` 직접 join 가능성,
`Recall@K`/`Violation@K` 계산 가능성이다.

이 단계에서는 reranking metric을 실행하지 않았다.

## 핵심 결과

Source prediction 자체는 reranking inventory에 충분하다.

| Source | In-scope source rows | Join key | Score/rank | Read policy |
| --- | ---: | --- | --- | --- |
| `vlsat_full_validation` | 441696 | complete | available | read-only |
| `open3dsg_recovery_relaxed_views_min2` | 321192 | complete | available | read-only |

하지만 H002 `S2_source_x_Ce` bridge는 아직 metric-ready가 아니다. 이유는 현재 H002
`C_e` score가 official GT/counterfactual materialization row에만 있고, source prediction
universe 전체에는 없기 때문이다.

| Source | Family | Source rows | H2 `C_e` direct join rate | Status |
| --- | --- | ---: | ---: | --- |
| `vlsat_full_validation` | `relative_vertical` | 73616 | 0.010596 | needs source-wide `C_e` materialization |
| `vlsat_full_validation` | `size_relative` | 73616 | 0.004619 | needs source-wide `C_e` materialization |
| `vlsat_full_validation` | `relative_horizontal` | 147232 | 0.106173 | needs source-wide `C_e` materialization |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 53532 | 0.008369 | needs source-wide `C_e` materialization |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 53532 | 0.003661 | needs source-wide `C_e` materialization |
| `open3dsg_recovery_relaxed_views_min2` | `relative_horizontal` | 107064 | 0.109916 | needs source-wide `C_e` materialization |

## Metric Readiness

| Metric / score | Current status | 이유 |
| --- | --- | --- |
| `Recall@K` with `S0_source_score` | computable | source score/rank와 official validation GT match가 있음 |
| `Violation@K` with H001 geometry | partially computable | `relative_vertical`, `proximity`, diagnostic `support_contact`는 checkable; `size_relative`, `relative_horizontal`은 H001 verification 없음 |
| `Recall@K` with `S2_source_x_Ce` | blocked | source-wide `C_e` score가 없음 |
| `Violation@K` with `S2_source_x_Ce` | blocked | source-wide `C_e`와 family별 violation label/materialization 필요 |
| `support_contact` success aggregation | blocked | diagnostic-only로 freeze됨 |

## 판단

지금 바로 source reranking metric을 실행하면 안 된다. `S0_source_score` baseline만 계산하는 것은
가능하지만, H002의 핵심 bridge인 `S2_source_x_Ce`와 비교할 수 없으므로 논문적 의미가 약하다.

따라서 다음 단계는 metric run이 아니라 source-wide `C_e` materialization protocol이다. Source
prediction universe 전체에 대해 model-safe `T_e`/`G_e` blocks를 만들고, hidden GT/violation
labels는 metric computation에만 사용하도록 분리해야 한다.

## 다음 단계

```text
compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory
```

이 단계에서는 source prediction universe keyed by `scan_id / subject_id / object_id /
predicate`에 대해 H002 `G_e`와 `C_e` 계산 경로를 freeze해야 한다.
