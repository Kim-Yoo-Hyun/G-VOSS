# v1 RGA Pilot

Last updated: 2026-06-22 KST

## Purpose

H002의 첫 단계는 relation source가 주는 하나의 confidence를 그대로 쓰지 않고,
`semantic score`, `geometry validity`, `coverage`, `uncertainty`, `relation reliability`로
분리할 수 있는지 확인하는 것이었다.

핵심 명제는 다음으로 고정했다.

```text
semantic score != geometry validity != relation reliability
```

## What Was Done

- `RGA(Relation-Geometric Agreement)` axis를 정의했다.
- Open3DSG train pilot row에서 `RGA-HL`, `RGA-LH`, uncertainty bucket을 만들었다.
- 초기 `semantic_only`, `geometry_only`, `semantic_plus_geometry`,
  `factorized_reliability_posterior` 비교군을 잡았다.
- Codex/bootstrap label 기반 posterior smoke와 shortcut probe를 수행했다.

## Result

RGA framing 자체는 유효했다. relation score가 높아도 geometry가 만족되지 않는 경우와,
relation score가 낮아도 geometry가 relation을 지지하는 경우를 분리해 볼 수 있었다.

하지만 초기 target은 rank, family, predicate construction과 강하게 얽혀 있었다.
posterior가 좋아 보이는 경우도 실제 reliability를 학습한 것이 아니라 rank/family proxy를
학습했을 가능성이 컸다.

## Problem

가장 큰 문제는 posterior 결합식이 아니라 target independence였다.

```text
model_gain may be explained by rank/family/predicate shortcut
```

따라서 v1 결과만으로는 factorized posterior가 relation reliability를 더 잘 설명한다고
주장할 수 없었다.

## Why Next Stage

pilot 규모와 bootstrap label로는 연구 주장에 필요한 독립 target을 만들 수 없었다.
그래서 full-train scale에서 relation family를 좁히고, label protocol과 geometry witness를
명확히 하는 v2로 넘어갔다.

## Boundary

v1은 H002 문제 정의와 RGA bucket의 diagnostic evidence다. Paper-level posterior evidence는
아니다.
