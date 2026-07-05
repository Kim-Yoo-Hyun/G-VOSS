# Main Validation Table Materialization

## Purpose

`main_validation_claim_table_lock`에서 고정한 H002 claim boundary를 기준으로,
이미 생성된 validation source-reranking metric을 paper caption-ready table로 정리했다.
이 단계는 새 metric run, threshold tuning, official test 사용이 아니다.

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
status = h002_main_validation_table_materialization_after_claim_lock_ready
selected_path = main_validation_table_materialized_select_review
validation_errors = 0
next_todo = compatibility_dataset_v3_main_validation_table_review_after_materialization
```

Materialized outputs:

- `main_validation_table.csv`: K = `{5,10,20,50,100}`에 대한 `S0_source_score` vs `S2_source_x_Ce`.
- `main_validation_table.md`: caption-ready markdown table.
- `source_family_caveats.csv`: 3개 source-family-K Recall@K regression caveat.
- `control_table_compact.csv`: `C_e only`, shuffled-`C_e`, wrong-`T` controls.
- `blocked_wording_checklist.csv`: official test, SOTA, open-set GT, uniform improvement, H003 main claim 차단 문구.

## Main Table Position

이 표는 H002의 main validation benchmark material로 사용할 수 있다.
단, 표현은 다음 boundary를 유지해야 한다.

- official 3DSSG validation split 기반이다.
- official 3DSSG test result가 아니다.
- Open3DSG는 open-vocabulary source지만 정량 평가는 closed 3DSSG label mapping 기준이다.
- `Violation@K`는 H002 custom geometry-consistency metric이다.
- `support_contact`는 primary success aggregation에 포함하지 않는다.
- H003 embedding은 future/optional extension이다.
