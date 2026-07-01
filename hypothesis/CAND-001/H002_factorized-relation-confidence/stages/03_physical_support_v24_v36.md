# Stage 03 Physical Support V24-V36

## Scope

이 문서는 기존 `v24`부터 `v36`까지의 physical relation-family, support/contact, cross-stratum
branch를 병합한 요약이다.

## 진행한 내용

- `v24`: `support_contact`, `relative_vertical`, `attachment_deferred` feasibility를 full train에서 확인했다.
- `v25-v30`: physical relation-family sampling plan, candidate mining, label fill, ingestion, target-independence audit, path decision을 진행했다.
- `v31-v33`: witness-matched repair plan과 capacity scan, path decision을 진행했다.
- `v34-v36`: controlled cross-stratum support/contact contrast plan, capacity scan, path decision을 진행했다.

## 핵심 결과

`support_contact`와 `relative_vertical`은 geometry witness를 만들기 쉬운 편이었고 row capacity도
충분했다. 하지만 posterior-ready target으로는 다음 문제가 반복됐다.

- reliability binary target이 positive-sparse였다.
- strict/diagnostic clear slice가 0개였다.
- same-witness HL/LH matching은 H002의 mismatch 정의와 맞지 않을 정도로 과도하게 제한적이었다.
- cross-stratum route에서는 raw quota가 충분했지만 `lying on` HL은 전부 `unsatisfied`, LH는 전부
  `satisfied`로 collapse되어 geometry_status shortcut이 생겼다.

`relative_vertical`은 geometry sanity/control family로는 유용하지만, factorized reliability를
증명하는 main target으로는 너무 geometry-determined인 경향이 있었다.

## 다음 단계로 넘어간 이유

Physical support/contact branch는 diagnostic target-construction evidence로 고정하고,
현재 geometry policy에서 unsupported였던 `attachment_deferred` relation을 typed witness schema로
다시 확인하기로 했다.

## Boundary

- `standing on`, `lying on`, `supported by`, `higher than`, `lower than`은 현재 H002에서 solved
  posterior target이 아니다.
- 이 branch의 가치는 geometry/status shortcut과 target-identifiability blocker를 보여준 데 있다.
