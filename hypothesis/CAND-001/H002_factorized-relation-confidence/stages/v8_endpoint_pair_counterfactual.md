# v8 Endpoint-Pair Counterfactual

Last updated: 2026-06-22 KST

## Purpose

v8은 같은 subject/object endpoint pair 안에서 predicate가 바뀌는 counterfactual 구조를 사용해
object/endpoint shortcut을 더 강하게 통제하려 했다.

## What Was Done

- `higher than/lower than`, `standing on/lying on` exact endpoint-pair 후보를 찾았다.
- 240-row endpoint-pair counterfactual queue를 만들었다.
- asset packet, replacement, label readiness/fill/ingestion/audit를 수행했다.
- 기존 v8 label이 약해 repair target을 추가 mining했고, 200-row repair batch를 만들었다.

## Result

endpoint-pair control은 v7보다 강했다.

```text
repair relation reliability binary rows = 80
class balance = 37 / 43
exact endpoint-pair balanced slice = 74 rows, 37 / 37
```

## Problem

남은 shortcut risk가 더 선명해졌다.

- `predicate_label`
- `rank_band_hidden`
- `machine_hint_hidden`

이 상태에서 posterior를 돌리면 factorized reliability가 아니라 predicate/rank construction shortcut을
학습할 수 있었다.

## Why Next Stage

v8에서 남은 risk가 predicate/rank/hint 축으로 좁혀졌다. 그래서 이 축들을 직접 통제할 수 있는지
확인하는 v9 feasibility scan으로 이동했다.

## Boundary

v8 repair target은 후보 수 측면에서는 유망하지만, target-independence gate를 통과하지 못했기
때문에 diagnostic-only다.
