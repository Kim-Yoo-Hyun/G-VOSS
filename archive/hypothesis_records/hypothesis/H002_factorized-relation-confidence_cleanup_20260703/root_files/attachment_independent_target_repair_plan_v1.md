# H002 Attachment Independent Target Repair Plan V1

Created: 2026-06-25

## Purpose

`attachment_independent_target_independence_audit_v1`에서 primary `p_rel/C_e` target이
positive-sparse로 막힌 뒤, 다음 repair route를 결정한다.

이 단계는 posterior를 학습하지 않고, target을 억지로 완화하지 않는다. 목표는 현재 target이
왜 막혔는지 정리하고, 새 H002 framework에 맞는 독립 target을 다시 만들기 위한 다음 mining
조건을 고정하는 것이다.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_target_repair_plan_v1.py
```

Default output:

```text
artifacts/attachment_independent_target_repair_plan_v1/
```

## Result

```text
status = h002_attachment_independent_target_repair_plan_v1_ready
selected_route = new_positive_anchor_mining_with_packet_materialization
next_todo = attachment_independent_positive_anchor_mining_plan_v1
validation_errors = 0
```

Capacity check:

```text
current_200 positive / negative = 17 / 91
all_v20_matched_298 positive / negative = 24 / 116
full_candidate_400 visible-rule positive / negative = 45 / 174
full_candidate_400 mixed_visible_pair_groups = 1
full_candidate_400 mixed_predicate_visible_pair_groups = 0
```

## Route Decision

| Route | Verdict | Reason |
| --- | --- | --- |
| use current 200 as-is | reject | only 17 positives and no clear controlled slice |
| use all v20-matched 298 | reject | only 24 positives, still below posterior-smoke threshold |
| materialize unmatched 102 and use all 400 | diagnostic-only | 45 positives possible, but attached-to remains sparse and predicate-visible-pair contrast is absent |
| relax uncertain / label policy | reject | would tune the target rather than repair independent evidence |
| new positive-anchor mining with packet materialization | selected | directly addresses independent accept-positive shortage |
| freeze attachment as diagnostic-only | fallback | use if positive-anchor mining also fails |

## Repair Requirements

```text
recommended_min_positive = 60
recommended_min_negative = 60
recommended_min_mixed_visible_pair_groups = 10
posterior_smoke_allowed = false
label_policy = do_not_relax_uncertain_to_accept
```

Required constraints:

- mine more high-precision accept-positive attachment candidates;
- materialize visual/mesh packet evidence before label fill;
- keep source score/rank, proxy role, cell id, and prior labels hidden from label decisions;
- report `attached to` and `hanging on` separately;
- if `attached to` cannot reach class mass, keep it diagnostic instead of forcing it into the primary target;
- rerun label fill, ingestion, and target-independence audit before any posterior smoke.

## Interpretation

현재 병목은 factorized combiner가 아니라 independent target construction이다.

이미 packet이 있는 v20-matched rows를 모두 써도 positive가 24개뿐이고, 400-row 후보 전체를
가정해도 predicate+visible-pair contrast가 0개다. 따라서 current attachment target으로
posterior를 학습하면 모델이 `C_e`를 배우는 것이 아니라 endpoint/object shortcut이나
construction artifact를 배울 가능성이 크다.

## Next

```text
attachment_independent_positive_anchor_mining_plan_v1
```
