# Test Benchmark Source Resolution

## Purpose

Validation table을 benchmark table에서 낮춘 뒤, H002 source-reranking 결과를
test benchmark로 승격할 수 있는 source route가 있는지 확인했다.

핵심 질문은 다음이다.

```text
Can we use an accepted official evaluation server or an independent
3DSSG relation test label/source-prediction pool for H002?
```

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight/
status = h002_test_benchmark_source_resolution_after_preflight_ready_blocked
selected_path = official_eval_server_not_confirmed_keep_validation_appendix_request_external_provenance
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution
```

## Decision

| 항목 | 판단 |
| --- | --- |
| accepted official evaluation server | not confirmed |
| independent relation test label | not confirmed |
| 3RScan scan-level test split | exists |
| scan-level split sufficient for H002 | false |
| local staged test candidates usable | false |
| relation-test source predictions | unavailable |
| experiments test run allowed | false |
| validation table position | appendix / secondary analysis only |

## Evidence

- 3RScan official repository exposes train/validation/test split links for
  scan-level data.
- 3DSSG official project/repository pages checked in this pass do not expose an
  accepted public relation evaluation server.
- Open3DSG documentation states that 3DSSG provides GT scene graphs for training
  and validation.
- Local Open3DSG source contains `test_scans_3rscan`, but its help text says the
  3RScan test scans are not labeled in 3DSSG, so that option cannot be treated
  as 3DSSG relation-GT benchmark evidence.
- H002 local preflight found no canonical `relationships_test.json`, found `2`
  non-empty staged test candidates that overlap validation scans, and found
  `0` official-test source rows.

## Interpretation

사용자 판단처럼 official evaluation server를 먼저 찾는 방향이 맞다. 다만 현재
확인된 사실은 “3RScan test split이 존재한다”이지, “3DSSG relation test GT나
public eval server가 H002에서 사용 가능하다”가 아니다.

따라서 현재 H002 source-reranking 결과는 validation-level appendix/secondary
evidence로 유지한다. Test benchmark table은 official server 또는 독립
relation-test provenance가 확인되기 전까지 만들지 않는다.

## Next

다음 단계는 metric runner가 아니라 external provenance request다. 필요한 것은
다음 중 하나다.

- official evaluation server route.
- official/independent `relationships_test.json` provenance.
- exact test split에 대한 VL-SAT/Open3DSG source prediction availability.
- split-disjointness proof for scan/object-pair/candidate ids.

