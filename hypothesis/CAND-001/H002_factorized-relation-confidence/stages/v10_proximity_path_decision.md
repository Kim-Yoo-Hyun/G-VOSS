# v10 Proximity Path Decision

Last updated: 2026-06-22 KST

## Purpose

v10 path decision은 v9 이후 H002를 어디로 진행할지 결정한 단계다. 핵심 질문은
`support_contact` / `relative_vertical` exact endpoint-pair target을 계속 밀 것인지,
아니면 relation type을 확장해 shortcut-free target을 다시 찾을 것인지였다.

## What Was Done

- v9 feasibility scan 결과를 path decision input으로 사용했다.
- v8 additional mining artifact의 proximity inventory를 함께 확인했다.
- 다음 선택지를 비교했다.
  - posterior smoke 즉시 실행
  - exact endpoint-pair v9 candidate mining 계속 진행
  - `support_contact`-only exact-pair fallback
  - endpoint-cell/rank-matched relaxation
  - `close by` / `proximity` relation-family expansion
  - attachment/multi-view 확장
  - relative horizontal 확장
  - H002 freeze

## Result

선택된 route는 다음이다.

```text
selected_path = v10_proximity_relation_family_feasibility_scan
next_todo = reliability_target_v10_proximity_relation_family_feasibility_scan
posterior_smoke_allowed = false
```

v9 exact endpoint-pair target은 diagnostic-only negative evidence로 고정한다.

## Key Evidence

v9는 count-limited failure가 아니었다.

```text
eligible_pairs = 9984
eligible_rows = 19968
strict_v9_exact_pair_feasible = false
rank_band -> predicate majority accuracy = 0.9229
rank baseline accuracy = 0.4976
rank NMI = 0.7505
```

반면 proximity inventory는 별도 feasibility scan을 시도할 만큼 충분하다.

```text
proximity_context_candidate_groups = 144443
strict_nonstruct_not_current_proximity_groups = 38313
kept_proximity_rows = 171324
future_proximity_preview_pairs = 20
future_proximity_preview_rows = 40
```

## Why Proximity Expansion

`close by`는 H002의 relation reliability claim을 support/vertical exact-pair 구조 밖에서
검증할 수 있는 relation family다. geometry witness가 distance/coverage 중심이라
`semantic score != geometry validity != relation reliability` 분해를 다시 테스트하기 좋다.

중요한 점은 이 확장이 "generality를 위해 아무 relation이나 추가"하는 것이 아니라,
v9에서 확인된 predicate/rank entanglement를 피할 수 있는 새로운 target construction route라는
점이다.

## Risks

- dense scene에서는 `close by`가 annotation sparsity와 relation noise를 많이 포함할 수 있다.
- distance가 가까워도 relation usefulness가 낮을 수 있다.
- source rank, object label pair, scan/context identity가 여전히 target shortcut이 될 수 있다.

## V10 Gate

v10은 posterior가 아니라 feasibility scan이다. 최소 조건은 다음이다.

- train-only.
- validation/test 사용 금지.
- `close by` proximity row만 별도 branch로 다룬다.
- 기존 v8/v9 support/vertical target과 섞지 않는다.
- rank-band, source-score bucket, subject/object label pair, endpoint-cell, scan id,
  distance bucket, coverage state shortcut audit를 수행한다.
- label fill이나 posterior smoke는 target-independence 가능성이 확인된 뒤에만 진행한다.

## Boundary

v10 path decision은 H002 가설을 지지하는 posterior evidence가 아니다. 다음 feasibility scan을
위한 route selection이다.
