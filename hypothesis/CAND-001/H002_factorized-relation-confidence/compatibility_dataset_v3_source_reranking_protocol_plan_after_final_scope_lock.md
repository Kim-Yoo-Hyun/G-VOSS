# Source Reranking Protocol Plan After Final Scope Lock

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock/
status = h002_compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock_ready
selected_path = source_reranking_protocol_ready_select_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan
```

## 목적

Final H002 scope lock 이후 `Recall@K`와 `Violation@K`를 downstream source-reranking
metric으로 다시 여는 protocol을 고정했다. 이 단계는 reranking metric을 실행하지 않는다.
대신 source score `Z_e`와 compatibility `C_e`를 어떤 위치에서 결합할지, 어떤 route를
포함/제외할지, 어떤 metric과 control을 사용할지 먼저 고정한다.

## 핵심 결정

- Official validation source candidates만 사용한다.
- Official test는 사용하지 않는다.
- Paper metric은 아직 promote하지 않는다.
- `C_e = compatibility(T_e, G_e)` 내부에는 `Z_e`를 넣지 않는다.
- Source score는 reranking stage에서만 `C_e`와 결합한다.
- `support_contact`는 diagnostic only이며 success aggregation에서 제외한다.
- `Recall@K`와 `Violation@K`는 downstream metric으로만 사용한다.

## Route Scope

| Route family | Source-reranking role | Inclusion |
| --- | --- | --- |
| `relative_vertical` | primary bridge candidate | include |
| `size_relative` | primary bridge candidate with feature caveat | include after H002 `G_e` materialization check |
| `relative_horizontal` | caveated frame-aware bridge | include as caveated or separate table |
| `proximity` | geometry-only route control | optional control if source candidates exist |
| `support_contact` | diagnostic only | exclude from success metric |

## Score Contract

| Score | Role | Formula | Claim |
| --- | --- | --- | --- |
| `S0_source_score` | baseline | source score or ranking score | source confidence baseline |
| `S1_Ce_only` | diagnostic | `C_e(T_e, G_e)` | compatibility ranking diagnostic |
| `S2_source_x_Ce` | primary bridge candidate | normalized source score * normalized `C_e` score | compatibility-aware source reranking bridge |
| `S3_source_plus_lambda_Ce` | ablation/future | `log(source_score) + lambda * normalized C_e` | risk/utility-style reranking if lambda is frozen before metrics |
| `C1_shuffled_Ce` | control | source score with shuffled `C_e` or `G_e` | must underperform real `C_e` bridge |
| `C2_wrong_predicate_Ce` | control | source score with wrong-`T` `C_e` | must underperform real predicate-geometry compatibility |

## Metric Contract

| Metric | Role | K grid | Boundary |
| --- | --- | --- | --- |
| `Recall@K` | primary downstream candidate | `5,10,20,50,100` | source-reranking bridge only |
| `Violation@K` | primary downstream candidate | `5,10,20,50,100` | geometry inconsistency after reranking, not primary `C_e` metric |
| `selected_count@K` | required sanity | `5,10,20,50,100` | prevents empty or coverage-shifted comparisons |
| `family_macro_delta` | required summary | `5,10,20,50,100` | aggregate-only reporting blocked |
| `control_delta` | required control | `5,10,20,50,100` | bridge invalid if controls do not collapse |

## Blocked

- target label or GT match flag in model-safe features
- `Violation@K` status in model-safe features
- `support_contact` success inclusion
- `Z_e` inside `C_e`
- official test
- post-hoc lambda tuning after validation metrics

## 다음 단계

다음 TODO는 source-reranking-specific source inventory다.

```text
compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan
```

여기서 VL-SAT/Open3DSG source candidates에 대해 source prediction join key, source score,
H002 `G_e` materialization 가능성, `C_e` score 계산 가능성, `Recall@K`/`Violation@K`
계산 가능성을 family별로 다시 점검해야 한다.
