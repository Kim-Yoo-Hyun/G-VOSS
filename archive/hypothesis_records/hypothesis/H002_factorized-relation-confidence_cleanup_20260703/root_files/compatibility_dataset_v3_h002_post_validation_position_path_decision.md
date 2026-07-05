# H002 Post-Validation Position Path Decision

## Purpose

이전 gate는 external test provenance가 없기 때문에 H002 validation result를
appendix/secondary로 낮춰 두었다. 하지만 VL-SAT와 Open3DSG의 공개 evaluation flow와
비교 가능한 source prediction은 3DSSG validation split 중심이므로, H002 main claim도
official 3DSSG validation split에서 진행하는 방향으로 재정의한다.

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision/
status = h002_post_validation_position_path_decision_ready
selected_path = promote_official_validation_as_main_comparative_claim_keep_test_blocked
validation_errors = 0
main_claim_split = official_3DSSG_validation_split
main_table_allowed = true_validation_benchmark
official_test_benchmark = false
next_todo = compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision
```

## Decision

선택한 방향은 다음이다.

- H002 main claim은 official 3DSSG validation split에서 진행한다.
- VL-SAT / Open3DSG validation predictions를 같은 GT 기준으로 비교한다.
- `Recall@K`와 `Violation@K`를 main validation table metric으로 사용한다.
- Open3DSG는 open-vocabulary relation source지만, 정량 평가는 closed-vocabulary
  3DSSG mapping 기준으로 명시한다.
- Official 3DSSG test result, leaderboard/SOTA, unconstrained open-set GT evaluation은
  계속 막는다.

## Why This Is Better

- 공개적으로 확인 가능한 relation GT는 validation split에 있다.
- VL-SAT와 Open3DSG source comparison을 같은 split과 같은 GT 기준에서 수행할 수 있다.
- 기존 공개 코드 흐름도 validation relation evaluation을 중심으로 구성되어 있다.
- test relation GT가 없다는 이유로 H002의 main empirical claim을 appendix로만 둘 필요는
  없다. 대신 `main validation benchmark`라고 정확히 표현하면 된다.

## Next

`compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision`에서 main table
caption, allowed baseline wording, blocked test/SOTA wording, source-family caveat를 고정한다.
