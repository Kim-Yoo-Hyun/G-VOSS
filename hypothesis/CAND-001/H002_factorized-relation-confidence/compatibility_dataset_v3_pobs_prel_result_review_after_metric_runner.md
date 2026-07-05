# H002 p_obs / p_rel Result Review After Metric Runner

## 목적

`p_obs/p_rel`을 H002 main framework의 selective decision layer로 포함할 수
있는지 확인하기 위해, protocol freeze 이후 실제 materialization, schema audit,
selective metric runner를 실행했다.

## 결과

```text
artifact_root = artifacts/compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner/
runtime_root = experiments/H002_compatibility_routing/pobs_prel_evaluation/latest/
status = h002_pobs_prel_result_review_after_metric_runner_ready
selective_metric_pass = true
paper_promotion_pass = false
validation_errors = 0
next_todo = compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review
```

Selective metric은 통과했다. `p_obs`는 synthetic missing-evidence controls를
강하게 abstain으로 보내고, `p_rel`은 observable original rows에서 최소 기준
AUROC를 넘었다.

다만 paper promotion은 아직 통과로 보지 않는다. 이유는 `p_rel` ECE가 사전
warning threshold `0.15`를 넘었고, unobservable label이 independent human label이
아니라 synthetic missing-evidence control이기 때문이다.

## 핵심 수치

| Metric | Value | Gate |
| --- | ---: | --- |
| `p_obs` AUROC | 1.000000 | pass |
| `p_obs` ECE@10 | 0.043647 | pass |
| `p_rel` AUROC | 0.724615 | pass |
| `p_rel` ECE@10 | 0.171030 | warn/fail for promotion |
| accept/reject/abstain macro-F1 | 0.778449 | pass |
| decision accuracy | 0.936476 | pass |
| missing-control abstain rate | 1.000000 | pass |
| AURC | 0.163562 | diagnostic |

## 해석

`p_obs/p_rel`은 H002 framework component로 유지할 수 있다. 특히 `p_obs`는
evidence-quality route가 abstain decision을 만들 수 있다는 stress-test는
통과했다.

그러나 이 결과를 paper의 독립 quantitative claim으로 바로 쓰면 안 된다.
현재 unobservable examples는 no-view, low-visibility, missing-mesh, shuffled-view
control로 만든 proxy label이다. 따라서 이 결과의 정확한 위치는 다음이다.

```text
selective decision stress-test passed
paper-ready calibrated p_obs/p_rel result not yet passed
```

## 다음 단계

1. CI와 calibration review를 추가한다.
2. qualitative examples를 뽑아 accept/reject/abstain의 실제 사례를 확인한다.
3. support/contact, attachment, containment에 대해 failure wording을 정리한다.
4. independent human observability label 없이 쓸 수 있는 claim boundary를 고정한다.
