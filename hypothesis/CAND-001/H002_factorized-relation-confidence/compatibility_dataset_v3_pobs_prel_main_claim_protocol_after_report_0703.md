# p_obs / p_rel Main-Claim Protocol After Report 0703

```text
status = h002_pobs_prel_main_claim_protocol_after_report_0703_ready
artifact_root = artifacts/compatibility_dataset_v3_pobs_prel_main_claim_protocol_after_report_0703/
validation_errors = 0
selected_path = include_pobs_prel_as_main_framework_claim_not_yet_quantitative_result
next_todo = compatibility_dataset_v3_pobs_prel_materialization_plan_after_protocol
```

## Purpose

H002의 main paper claim을 단순 `C_e` reranking에서 selective reliability
decision까지 확장한다.

```text
Stage 1: C_e = compatibility(T_e, G_e)
Stage 2: S2 = source_score(Z_e) * C_e
Stage 3: p_obs / p_rel selective decision
```

이 단계의 핵심은 `p_obs`와 `p_rel`을 main framework에 포함하되, 아직
정량 결과가 끝났다고 주장하지 않는 것이다.

## Decision

`p_obs/p_rel`은 H002 main method에 포함한다.

Allowed claim:

- `Q_e`는 evidence quality / observability를 담당한다.
- `p_obs`는 현재 evidence로 relation을 판단할 수 있는지 예측한다.
- `p_rel`은 observable edge에 대해 relation reliability를 예측한다.
- 최종 decision은 accept / reject / abstain으로 분리한다.

Blocked claim until metric passes:

- calibrated `p_obs/p_rel` 성능이 검증 완료됐다.
- abstain decision이 official validation에서 성능을 개선했다.
- support/contact, attachment, containment hard route가 해결됐다.

## Completion Boundary

사용자가 제시한 작업 목록은 `p_obs/p_rel`을 main claim에 넣기 위한
protocol freeze를 완료하는 데 충분하다. 그러나 p_obs/p_rel 작업 전체가
마무리되려면 아래 세 단계가 모두 필요하다.

| Stage | 완료 조건 | 현재 상태 |
| --- | --- | --- |
| Protocol freeze | `Q_e`, labels, targets, metrics, controls, failure routes 고정 | complete |
| Materialization / evaluation | model-safe views, hidden labels, schema audit, metric runner 생성 및 실행 | pending |
| Paper promotion | selective metric pass, CI, qualitative example, failure wording 고정 | pending |

따라서 이 단계 완료는 "main framework claim 준비 완료"이지,
"p_obs/p_rel quantitative result 완료"는 아니다.

## Frozen Rule

```text
p_obs low -> abstain
p_obs high + p_rel high -> accept
p_obs high + p_rel low -> reject
```

`p_obs`는 relation truth를 직접 판단하지 않는다. `p_obs`는 판단 가능성만
담당한다. `p_rel`은 `p_obs`가 충분한 edge에서만 accept/reject를 담당한다.
