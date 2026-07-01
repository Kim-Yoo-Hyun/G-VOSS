# H002 Grouped Evaluation Result Review After Runner

## Status

```text
status = h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready
selected_path = grouped_review_ready_after_feature_repair_select_claim_boundary_review
validation_errors = 0
next_todo = compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

## Purpose

Grouped evaluation runner가 만든 internal candidate-pool metric을 바로 claim으로
올리지 않고, relation family별로 어떤 결과가 claim-supporting, partial,
failed, repair-needed인지 판정했다.

이 단계는 여전히 official validation/test가 아니며 paper-level result도 아니다.

## Inputs

```text
experiments/H002_compatibility_routing/evaluation/latest/route_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/control_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/eval_manifest.json
artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol/summary.json
```

## Outputs

```text
artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/summary.json
artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/family_decisions.csv
artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/predicate_review.csv
artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/report.md
artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/validation_errors.jsonl
```

## Verdict

Feature extractor repair 이후 aggregate로는 `T_e x G_e` compatibility signal이 강하다.
하지만 family-level boundary는 여전히 필요하다.

| Family | Heldout AUROC | Status | Current paper role |
| --- | ---: | --- | --- |
| `relative_horizontal` | 0.969568 | claim-supporting | main compatibility-route evidence |
| `relative_vertical` | 0.999921 | claim-supporting | main compatibility-route evidence |
| `size_relative` | 0.999969 | claim-supporting | main compatibility-route evidence |
| `support_contact` | 0.610960 | partial | challenging compatibility-route evidence |

## Interpretation

`size_relative`, `relative_vertical`, `relative_horizontal`은 wrong-`T_e`와
shuffled-`G_e` control이 무너지므로 현재 H002의 compatibility-route evidence로
사용할 수 있다.

`support_contact`는 heldout에서 `M4`가 semantic-only, geometry-only, concat,
wrong-`T_e`, shuffled-`G_e`보다 낫지만 절대 AUROC가 낮다. 따라서 solved
family가 아니라 challenging compatibility route로 표현해야 한다.

`relative_vertical`은 feature extractor repair 이후 복구됐다. 기존 실패는
`center_delta_z`가 raw geometry value가 아니라 availability mask를 읽은 구현 문제였다.

## Boundary

- official validation/test 사용 없음.
- paper metric 생성 없음.
- `p_obs` / `p_rel` claim 생성 없음.
- `Z_e` / `Q_e`는 main `C_e`에 사용하지 않음.
- H001 artifact 수정 없음.

## Next

```text
compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review
```

Claim lock 전에는 repaired grouped result를 기준으로 paper claim boundary를 다시
정리해야 한다. 특히 `support_contact`는 partial/challenging으로 남겨야 한다.
