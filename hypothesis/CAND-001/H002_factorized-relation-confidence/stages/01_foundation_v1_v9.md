# Stage 01 Foundation V1-V9

## Scope

이 문서는 기존 `v1`부터 `v9`까지의 개별 stage log를 병합한 요약이다. 세부 row-level
artifact와 원본 수치는 `artifacts/` 아래의 각 `summary.json` / `report.md`가 소유한다.

## 진행한 내용

- `v1`: RGA axis와 초기 factorized posterior pilot을 만들었다.
- `v2`: full-train `support_contact` / `relative_vertical` pipeline을 확인했다.
- `v3`: positive-anchor와 object/endpoint-controlled target을 시도했다.
- `v4`: matched contrast target을 만들었다.
- `v5`: object/geometry cell contrast를 확인했다.
- `v6`: `accept/reject/abstain` schema와 shortcut-controlled queue를 설계했다.
- `v7`: object-cell evidence contrast를 확장했다.
- `v8`: same endpoint-pair predicate counterfactual target을 만들었다.
- `v9`: predicate/rank/hint controlled exact-pair feasibility를 확인했다.

## 핵심 문제

초기 방향은 relation reliability를 factorized posterior로 바로 검증하려 했지만, target 자체가
독립적이지 않았다. 반복적으로 다음 문제가 확인됐다.

- `predicate_label`, `rank_band_hidden`, `machine_hint_hidden` shortcut.
- object label / endpoint-pair shortcut.
- positive / negative class mass 부족.
- exact endpoint-pair 안에서 rank와 predicate가 구조적으로 얽힘.

`v9`에서 candidate count는 충분했지만 `rank_band -> predicate` majority accuracy가 매우 높아
posterior가 factorized reliability를 배우는 것이 아니라 construction shortcut을 배울 가능성이
크다고 판단했다.

## 다음 단계로 넘어간 이유

support/contact와 vertical exact-pair route는 diagnostic-only로 고정하고, relation-family를
확장해 `close by` / proximity branch를 확인하기로 했다. 따라서 다음 병합 stage는
`02_proximity_v10_v23.md`다.

## Boundary

- Train-only hypothesis-stage evidence.
- Validation/test row 사용 없음.
- Posterior smoke는 target-independence gate 전까지 금지.
- 원래 개별 stage logs는 이 병합 문서와 `summary_branch_v2.md`로 대체된다.
