# H002 Repaired Grouped-Eval Claim Boundary Review

## Status

```text
status = h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_ready
selected_path = claim_boundary_locked_select_official_validation_test_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review
```

## Purpose

Feature extractor repair 이후의 grouped evaluation 결과를 바로 paper claim으로
올리지 않고, hypothesis-stage에서 어떤 claim만 허용되는지와 어떤 claim은 아직
blocked인지 명시적으로 잠갔다.

이 단계는 metric runner가 아니라 claim-boundary review다.

## Inputs

```text
artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis/summary.json
artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/summary.json
experiments/H002_compatibility_routing/evaluation/latest/eval_manifest.json
```

## Outputs

```text
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/summary.json
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/claim_boundary.csv
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/family_claim_roles.csv
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/blocked_claims.csv
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/promotion_gaps.csv
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/paper_wording.md
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/report.md
artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/validation_errors.jsonl
```

## Allowed Claims

현재 허용되는 것은 hypothesis-stage internal candidate-pool claim이다.

1. `C_e = compatibility(T_e, G_e)`는 internal grouped holdout에서 `T_e` only,
   `G_e` only, plain `T_e + G_e` concat, wrong-`T_e`, shuffled-`G_e`보다 강한
   discrimination을 보인다.
2. 모든 relation에 하나의 fixed semantic-geometry fusion을 쓰는 것이 아니라,
   relation family별 evidence route가 다르다는 주장을 지지한다.
3. `support_contact`는 solved family가 아니라, contact/pose route가 어렵고 더 좋은
   local contact/pose evidence가 필요하다는 partial/challenging evidence다.

## Family Claim Roles

| Family | Predicates | Status | Route type | Heldout M4 AUROC | Claim role |
| --- | --- | --- | --- | ---: | --- |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | claim-supporting | predicate-geometry direction route | 0.969568 | main internal compatibility evidence |
| `relative_vertical` | `higher than`, `lower than` | claim-supporting | predicate-geometry axis-order route | 0.999921 | main internal compatibility evidence |
| `size_relative` | `bigger than`, `smaller than` | claim-supporting | predicate-geometry size route | 0.999969 | main internal compatibility evidence |
| `support_contact` | `standing on`, `lying on` | partial | challenging contact/pose route | 0.610960 | partial/challenging evidence |

## Blocked Claims

현재 blocked 상태인 claim은 다음과 같다.

- H002가 official 3DSSG / VL-SAT / Open3DSG validation 또는 test relation prediction
  metric을 개선한다는 주장.
- calibrated `p_rel` 또는 selective `p_obs` reliability를 추정한다는 주장.
- `support_contact`를 해결했다는 주장.
- 모든 3DSSG relation type으로 일반화된다는 주장.
- aggregate `M4` AUROC만으로 H002가 성립했다는 주장.

## Interpretation

수리된 grouped result는 H002의 핵심 방향을 강화한다. 다만 강화되는 것은
`C_e` compatibility representation의 내부 검증이지, 아직 full paper-level relation
reliability framework 전체가 아니다.

핵심 문장은 다음으로 제한해야 한다.

```text
Predicate-geometry compatibility can be learned for selected 3D Scene Graph
relation families when semantic content T_e and predicate-independent geometry
evidence G_e are separated.
```

그리고 바로 다음 문장에는 반드시 boundary를 붙인다.

```text
This is currently supported on an internal candidate-pool grouped holdout, not
official validation/test, and does not yet instantiate calibrated p_rel/p_obs.
```

## Boundary

- official validation/test 사용 없음.
- paper-level metric 생성 없음.
- `C_e` claim만 hypothesis-stage로 허용.
- `p_obs` / `p_rel` claim은 아직 blocked.
- `Z_e` / `Q_e`는 diagnostic-only.
- H001 artifact 수정 없음.

## Next

```text
compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review
```

다음 단계에서는 official validation/test로 어떻게 옮길지 protocol을 먼저 정의해야 한다.
현재 내부 candidate-pool metric을 그대로 paper metric으로 승격하면 안 된다.
