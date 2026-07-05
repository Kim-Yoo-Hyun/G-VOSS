# H002 CI / Qualitative / Failure Wording After p_obs / p_rel Review

## 목적

`p_obs/p_rel` selective metric이 통과한 뒤, 이 결과를 paper claim으로 어디까지
사용할 수 있는지 검토했다.

## 결과

```text
artifact_root = artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review/
status = h002_ci_qualitative_failure_wording_after_pobs_prel_review_ready
selected_path = keep_pobs_prel_as_framework_component_ci_qualitative_wording_ready
paper_promotion_pass = false
validation_errors = 0
next_todo = compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan
```

Bootstrap CI:

| Metric | Point | 95% CI |
| --- | ---: | --- |
| `p_obs` AUROC | 1.000000 | [1.000000, 1.000000] |
| `p_rel` AUROC | 0.724615 | [0.715937, 0.730900] |
| decision macro-F1 | 0.778449 | [0.773312, 0.782656] |
| missing-control abstain rate | 1.000000 | [1.000000, 1.000000] |

## 해석

`p_obs/p_rel`은 H002 framework component로 유지한다. 다만 calibrated
quantitative paper-result claim은 아직 올리지 않는다.

이유:

- unobservable examples are synthetic missing-evidence controls.
- independent human observability labels were not used.
- `p_rel` calibration warning remains.
- support/contact, attachment, containment are not solved by this selective
  stress test.

## 다음 단계

H002를 독립 paper outline으로 열지, H001/H002 integration 후보로 둘지, 혹은
hypothesis artifact로 유지할지 결정한다.
