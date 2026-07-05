# Test Benchmark Preflight

## 2026-07-02 Decision Update

목적:

Validation table을 appendix/secondary analysis로 낮춘 뒤, H002 benchmark table을 test set으로
만들 수 있는지 preflight했다. 이 단계는 test metric을 실행하는 단계가 아니라, 독립 test label,
split disjointness, test source prediction, frozen protocol 준비 여부를 판정하는 hypothesis gate다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade/
status = h002_test_benchmark_preflight_after_validation_downgrade_ready_blocked
selected_path = test_benchmark_blocked_select_independent_test_provenance_or_eval_server
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight
```

Decision:

- Test benchmark is not ready.
- Validation table remains appendix/secondary analysis only.
- Experiments-level test run is not allowed yet.
- Main blockers are independent test provenance and test source prediction availability.

Key findings:

- canonical `local_dataset/3DSSG_subset/relationships_test.json` does not exist.
- non-empty staged `relationships_test.json` candidates exist, but they overlap canonical validation scans.
- current source-reranking materialization has `762888` official-validation rows and `0` official-test rows.
- therefore current files cannot support an independent test benchmark table.

Gate status:

| Gate | Status | Reason |
| --- | --- | --- |
| `test_label_provenance` | fail | canonical test missing; staged non-empty test candidates overlap validation scans |
| `split_disjointness` | fail | validation-alias candidates observed |
| `test_source_prediction_availability` | fail | official-test source rows are 0 |
| `frozen_Ce_model_and_features` | partial | validation model/schema exists, but no test-specific frozen artifact contract |
| `normalization_freeze` | partial | validation normalization exists, but test policy must be frozen |
| `test_materialization_schema_audit` | pending_blocked | no official-test materialization exists |
| `metric_and_claim_freeze` | partial | validation wording exists, but test benchmark wording/CI policy not frozen |
| `single_final_test_run_policy` | pending | must be documented before any test run |

Next step:

`compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight`에서 독립 test source를
확보할 수 있는지 결정한다. 가능한 경로는 다음 중 하나다.

- official evaluation server 확인.
- 독립 test label/provenance 확인.
- test benchmark를 포기하고 validation-only appendix evidence로 유지.
- source-reranking benchmark를 Open3DSG/VL-SAT validation bridge로만 제한.
