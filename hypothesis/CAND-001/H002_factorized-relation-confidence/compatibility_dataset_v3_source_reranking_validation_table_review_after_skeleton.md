# Source Reranking Validation Table Review

## 2026-07-02 Decision Update

목적:

Validation table skeleton을 paper benchmark table로 사용할지 review했다. 사용자 결정에 따라
최종 benchmark table은 test set으로 만들고, 현재 validation table은 낮춰서
appendix/secondary analysis로만 사용하도록 고정했다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton/
status = h002_source_reranking_validation_table_review_after_skeleton_ready
selected_path = downgrade_validation_table_select_test_benchmark_preflight
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade
```

Decision:

- `source_reranking_validation_table`은 main benchmark table이 아니다.
- Paper에 쓰더라도 appendix 또는 secondary validation analysis로만 둔다.
- Main benchmark table은 independent test set 또는 accepted official evaluation server로만 만든다.
- 현재 test benchmark는 아직 ready가 아니다.

Local test probe:

- canonical `local_dataset/3DSSG_subset/relationships_test.json`은 존재하지 않는다.
- Open3DSG staged runtime 아래 `relationships_test.json` 후보들이 존재하지만, non-empty 후보는
  canonical validation scan과 전부 overlap한다.
- 따라서 staged `relationships_test.json`은 provenance와 split-disjointness가 확인되기 전까지
  독립 test benchmark로 사용할 수 없다.

Pre-experiment gates:

1. `test_label_provenance`: 독립 official test label 또는 official evaluation server 확인.
2. `split_disjointness`: train/validation/test scan, object-pair, candidate-id overlap audit.
3. `source_prediction_availability`: VL-SAT/Open3DSG test source prediction availability 확인.
4. `frozen_Ce_model_and_features`: `C_e` model, feature schema, family scope, score IDs, K grid freeze.
5. `normalization_freeze`: source score / `C_e` normalization을 test label이나 post-hoc test statistic으로 조정하지 않도록 고정.
6. `test_materialization_schema_audit`: model-safe/source-rank/hidden metric views 분리와 blocked-field audit.
7. `metric_and_claim_freeze`: Recall@K, Violation@K, controls, family aggregation, CI, wording freeze.
8. `single_final_test_run_policy`: test 실행 후 method/threshold/lambda/feature/family/wording 변경 금지.

Next step:

`compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade`에서 위 gate들을
실제 파일/프로토콜 기준으로 검증한다.
