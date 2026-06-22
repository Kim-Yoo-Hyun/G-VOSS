# v9 Predicate/Rank/Hint Feasibility

Last updated: 2026-06-22 KST

## Purpose

v9는 exact endpoint-pair design을 유지하면서 `predicate_label`, `rank_band_hidden`,
`machine_hint_hidden`까지 동시에 통제할 수 있는지 확인했다.

## What Was Done

- full train queue에서 기존 repair exact keys와 structural/generic endpoints를 제외하고 재스캔했다.
- `relative_vertical_higher_lower`와 `support_contact_standing_lying` exact pair를 집계했다.
- rank/hint/predicate control gate와 majority shortcut probe를 계산했다.

## Result

후보 수 자체는 충분했다.

```text
eligible_pairs = 9984
eligible_rows = 19968
relative_vertical_higher_lower_pairs = 47
support_contact_standing_lying_pairs = 9937
four_predicate_balanced_rows_upper_bound = 188
strict_v9_exact_pair_feasible = false
```

하지만 exact pair 내부에서 rank와 predicate가 구조적으로 얽혀 있었다.

```text
rank_band -> predicate majority accuracy = 0.9229
baseline = 0.4976
```

## Problem

이 문제는 row count 부족이 아니다. exact endpoint-pair 후보는 많지만, source rank pattern이
predicate를 너무 잘 설명한다. 따라서 strict v9 exact-pair target을 primary posterior target으로
쓰면 안 된다.

## Why Next Stage

다음 단계는 posterior 결합식을 바꾸는 것이 아니라 target path decision이다.

선택지는 다음이다.

- exact endpoint-pair 조건을 완화하고 endpoint-cell/rank-matched target으로 전환한다.
- `support_contact`-only controlled target으로 좁혀서 feasibility를 다시 확인한다.
- current exact-pair v9를 diagnostic-only negative evidence로 고정한다.
- `close by` proximity branch는 core target이 정리된 뒤 generality branch로 별도 진행한다.

## Boundary

v9는 H002 가설 실패가 아니라 target construction failure를 보여준다. Posterior smoke remains
blocked until target-independence passes.
