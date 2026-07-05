# Validation-Only Position Lock After No External Response

## Purpose

External response ingestion에서 official evaluation server, independent
`relationships_test.json`, 또는 official validation-as-standard protocol이 확인되지
않았다. 따라서 현재 H002 source-reranking 결과의 논문 내 위치와 claim boundary를
보수적으로 잠근다.

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response/
status = h002_validation_only_position_lock_after_no_external_response_ready
selected_path = validation_only_appendix_secondary_lock_keep_test_benchmark_blocked
validation_errors = 0
paper_position = appendix_or_secondary_analysis
official_test_benchmark = false
next_todo = compatibility_dataset_v3_h002_post_validation_position_path_decision
```

Generated files:

| File | 내용 |
| --- | --- |
| `paper_position_lock.csv` | validation-only paper position and blocked wording |
| `allowed_claims.csv` | 허용 가능한 validation-level claim |
| `blocked_claims.csv` | 금지할 official-test / SOTA / open-set claim |
| `reopen_conditions.csv` | test path를 다시 열 수 있는 조건 |
| `source_vocab_boundary.csv` | VL-SAT / Open3DSG source와 evaluation-GT boundary |
| `metric_position.csv` | `Recall@K`, `Violation@K`, `C_e` metric의 논문 내 역할 |
| `wording_guidance.md` | allowed / blocked wording guidance |
| `summary.json` | lock summary |

## Locked Position

- 현재 H002 source reranking은 official 3DSSG validation split 기반 custom
  evaluation이다.
- 결과는 appendix 또는 secondary analysis로 둔다.
- Official 3DSSG test benchmark 결과가 아니다.
- Validation table을 final benchmark table로 쓰지 않는다.

## Allowed Claims

- VL-SAT / Open3DSG validation predictions에 H002 reranking을 적용했다.
- Frozen custom validation protocol에서 `Recall@K`, `Violation@K` 변화를 보고한다.
- Open3DSG는 open-vocabulary relation source로 사용하되, 정량 평가는 closed-vocabulary
  3DSSG label mapping 기준이다.

## Blocked Claims

- official 3DSSG test result.
- SOTA / leaderboard claim.
- unconstrained open-set relation-GT evaluation.
- validation table as final benchmark table.
- prediction-only 3RScan test scan export를 `Recall@K` benchmark로 사용하는 claim.

## Reopen Conditions

다음 중 하나가 공식 증빙으로 들어오면 test benchmark route를 다시 열 수 있다.

- official `relationships_test.json` provenance.
- hidden evaluation server.
- maintainer / official documentation statement that validation is the standard
  reporting split.
- 별도 human-audited reliability benchmark protocol. 단, 이 경우 official 3DSSG test가
  아니라 별도 benchmark claim으로 분리해야 한다.
