# Source Reranking Metric Protocol Freeze

## 2026-07-02 Decision Update

목적:

Source-wide `C_e` materialization과 schema audit이 통과된 뒤, `Recall@K`와
`Violation@K`를 실제로 계산하기 전에 score definition, K grid, family aggregation,
normalization, and control protocol을 고정했다. 이 단계는 metric runner 실행이 아니라
paper-level downstream source-reranking metric을 안전하게 실행할 수 있는지 확인하는
protocol gate다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit/
status = h002_source_reranking_metric_protocol_freeze_after_schema_audit_ready
selected_path = source_reranking_metric_protocol_frozen_select_metric_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze
```

고정한 score contract:

| Score | Role | Main use |
| --- | --- | --- |
| `S0_source_score` | source baseline | source score/rank만 사용 |
| `S1_Ce_only` | diagnostic | `C_e_score(T_e, G_e)`만 사용 |
| `S2_source_x_Ce` | primary bridge | normalized source score와 normalized `C_e`를 곱함 |
| `S3_log_source_plus_Ce` | fixed ablation | lambda fixed to `1.0`, tuning 금지 |
| `C1_source_x_shuffled_Ce` | negative control | shuffled `C_e` 결합 |
| `C2_source_x_wrong_T_Ce` | negative control | wrong-`T` `C_e` 결합 |

Metric protocol:

- Primary downstream metrics: `Recall@K`, `Violation@K`, `Selected@K`.
- K grid: `{5, 10, 20, 50, 100}`.
- Ranking scope: `source_id + subgraph_id + route_family`.
- Primary score: `S2_source_x_Ce`.
- Primary success families: `relative_vertical`, `size_relative`.
- `relative_horizontal`: caveated frame-aware separate table.
- `proximity`: geometry-only control.
- `support_contact`: diagnostic only; success aggregation에서 제외.

Boundary:

- Source reranking metric은 아직 실행하지 않았다.
- Official test는 사용하지 않았다.
- `C_e = compatibility(T_e, G_e)` 내부에는 `Z_e`를 넣지 않는다.
- Source score/rank `Z_e`는 `S2` reranking stage에서만 결합한다.
- Validation 결과를 보고 lambda를 tuning하지 않는다.
- `p_obs` / `p_rel` claim은 아직 열지 않는다.

다음 step:

`compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze`에서
Docker metric runner를 구현/실행해 `S0`, `S1`, `S2`, controls의 `Recall@K`와
`Violation@K`를 family-wise로 계산한다.
