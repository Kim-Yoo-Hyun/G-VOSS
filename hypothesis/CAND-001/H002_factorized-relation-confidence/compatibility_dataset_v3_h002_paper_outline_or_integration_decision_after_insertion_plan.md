# H002 Paper Outline / Integration Decision After Insertion Plan

## 목적

H002를 독립 paper outline으로 열지, H001 manuscript에 통합할지, 또는 hypothesis
artifact로만 유지할지 결정했다.

## 결과

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan/
status = h002_paper_outline_or_integration_decision_after_insertion_plan_ready
selected_path = open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root
validation_errors = 0
next_todo = compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision
```

선택한 방향은 H002를 독립 paper-outline candidate로 유지하는 것이다. 지금은 H001
manuscript를 수정하지 않고, 새 top-level paper folder도 만들지 않는다.

## 판단 이유

- H002는 `T_e/G_e/Z_e/Q_e`, `C_e`, `p_obs/p_rel`을 중심으로 한 factorized
  compatibility/reliability framework다.
- H001/GeoCalib는 이미 calibrated geometry-consistency reranking paper로 scope가
  고정돼 있다.
- H002를 H001에 바로 섞으면 H001의 claim이 흐려지고, H002의 남은 caveat까지
  H001 paper가 떠안게 된다.
- H002는 validation-level evidence가 충분해 독립 outline 후보로는 가치가 있다.
- 다만 official-test/SOTA, calibrated `p_obs/p_rel`, support/contact solved claim은
  여전히 막혀 있으므로 새 paper workspace를 바로 만들지는 않는다.

## 다음 단계

독립 outline gap review를 진행한다. 여기서는 H002가 실제 paper workspace로 승격되기
전에 부족한 표, figure, related work, ablation, limitation wording을 점검한다.
