# Support/Contact Harder Route Metric Result Review After Runner

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner/
status = h002_support_contact_harder_route_metric_result_review_after_runner_ready
selected_path = freeze_support_contact_harder_route_as_diagnostic_failure_taxonomy
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review
```

## 목적

`support_contact` hard route에서 internal dev는 `M4_TxG_compatibility` signal을 보였지만,
official validation에서는 `M4`가 무너진 이유를 검토했다. 이 단계의 목적은 모델을 더
강하게 돌리는 것이 아니라, 현재 support/contact route를 paper success로 올릴 수 있는지
판단하는 것이다.

## 결과

핵심 결과는 다음과 같다.

| 항목 | 값 |
| --- | ---: |
| internal dev `M4` AUROC | 0.721356 |
| official validation `M4` AUROC | 0.077539 |
| official validation geometry-only AUROC | 0.500000 |
| official validation wrong-`T` AUROC | 0.922461 |
| paired `M4` accuracy | 0.182505 |
| paired wrong-`T` accuracy | 0.817495 |

Official validation에서 correct predicate보다 wrong predicate가 훨씬 잘 맞는다. 즉 현재
support/contact hard route는 성공 결과가 아니라 score direction이 뒤집힌 failure case다.

## 원인 판단

1. `wrong-T inversion`이 가장 큰 blocker다.
   - `M4` AUROC는 `0.077539`이고 wrong-`T` AUROC는 `0.922461`이다.
   - paired group에서도 `M4`는 `0.182505`, wrong-`T`는 `0.817495`다.
   - 이는 post-hoc score flip으로 구제할 문제가 아니라 target/feature convention mismatch로 봐야 한다.

2. Train-aligned `G_e`와 official validation `G_e` 분포가 다르다.
   - `support_contact_likelihood_proxy` official outside train range: `0.694147`
   - `xy_overlap_min_ratio` official outside train range: `0.950913`
   - 따라서 train-side hard-route target과 official validation materialization이 같은 evidence regime이라고 보기 어렵다.

3. Official validation target semantics와 train-side target semantics가 다르다.
   - train-aligned rows는 `standing on`/`lying on`이 각 label에서 균형적이다.
   - official validation은 GT predicate + same-geometry counterfactual 구조라서
     `standing on` positive가 많고 `lying on` negative가 많다.
   - 이 차이가 support/contact convention inversion을 만들었을 가능성이 높다.

## 결론

현재 H002 방향이 전체적으로 잘못됐다고 보지는 않는다. 실패는 H002의 핵심 원리
`T_e`, `G_e`, `C_e` 분리 자체를 반박한 것이 아니라, support/contact hard route의
target/feature contract가 official validation으로 transfer되지 않는다는 국소적 failure다.

따라서:

- `support_contact` solved claim은 금지한다.
- 현재 support/contact hard route는 diagnostic / failure taxonomy로 고정한다.
- official validation score를 post-hoc flip해서 성공처럼 쓰지 않는다.
- H002 core route인 `relative_vertical`, `size_relative`, `relative_horizontal` evidence는 유지한다.
- support/contact를 다시 시도하려면 target/feature contract를 처음부터 재설계해야 한다.

## 다음 단계

다음 TODO는 path decision이다.

```text
compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review
```

여기서 결정할 것은 두 가지다.

1. support/contact를 diagnostic/failure taxonomy로 고정하고 H002 paper claim을 clean route 중심으로 제한한다.
2. 또는 support/contact target/feature contract를 새로 설계한다.

현재 판단은 1번이 더 안전하다. 2번은 가능하지만, 기존 결과를 수리하는 수준이 아니라
새 target construction으로 다시 시작해야 한다.
