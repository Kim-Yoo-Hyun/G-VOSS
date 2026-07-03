# Source Reranking Validation Table Skeleton

## 2026-07-02 Decision Update

목적:

Source-reranking claim boundary lock 이후, 그 boundary를 어기지 않는 validation table
skeleton을 만들었다. 이 단계는 새 metric을 계산하거나 final paper result로 승격하는 단계가
아니라, `S2_source_x_Ce` source-reranking 결과를 어떤 표 구조로 보여줄 수 있는지 고정하는
draft 단계다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock/
status = h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_ready
selected_path = source_reranking_validation_table_skeleton_ready_select_table_review
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton
```

Table skeleton:

- `primary_tradeoff_table.csv`: `S2_source_x_Ce` vs `S0_source_score` weighted primary
  Recall@K / Violation@K tradeoff.
- `control_table.csv`: `C_e` only, shuffled-`C_e`, wrong-`T` controls.
- `source_family_caveat_table.csv`: 반드시 보고해야 하는 3개 Recall@K regression cell.
- `source_family_full_table.csv`: 20개 source-family-K cell 전체.
- `table_position_lock.csv`: main text / appendix / blocked position decision.

Primary tradeoff:

| K | Delta Recall@K | Delta Violation@K |
| ---: | ---: | ---: |
| 5 | +0.007937 | -0.240690 |
| 10 | +0.041950 | -0.229859 |
| 20 | +0.081633 | -0.243091 |
| 50 | +0.103175 | -0.259199 |
| 100 | +0.004535 | -0.142873 |

Required caveat:

20개 source-family-K cell 중 3개에서 Recall@K가 소폭 낮아졌다. 모든 caveat cell에서
Violation@K는 개선됐다.

| Source | Family | K | Delta Recall@K | Delta Violation@K |
| --- | --- | ---: | ---: | ---: |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 5 | -0.010204 | -0.265888 |
| `vlsat_full_validation` | `relative_vertical` | 5 | -0.017949 | -0.047810 |
| `vlsat_full_validation` | `size_relative` | 50 | -0.011765 | -0.216954 |

Decision:

이 table skeleton은 validation-level deployability evidence로 사용할 수 있다. 단, final paper
result, official test result, SOTA/full 3DSSG improvement, uniform improvement,
`C_e`-alone deployable score, `support_contact`, `p_obs`, `p_rel` claim으로 확장하면 안 된다.

Next step:

`compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton`에서 이 표가
main text secondary validation table로 충분한지, appendix-only로 낮춰야 하는지 review한다.
