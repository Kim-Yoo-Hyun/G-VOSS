# H002 Proximity Close-By Schema Shortcut Audit

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut
validation_errors = 0
critical_blockers = 5
learned_smoke_allowed = false
main_claim_verdict = blocked_for_close_by_current_target
next_todo = compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

## Decision

`close by` materialized target은 schema leakage는 통과했지만, shortcut audit에서 막혔다.
현재 target은 `distance_only`와 `p_geom_valid_rule`이 거의 완전히 풀 수 있으므로, 이 상태로는
`close by`를 H002 main claim으로 올리면 안 된다.

즉, 현재 `close by` 결과는 다음으로 해석한다.

```text
close by = proximity-family diagnostic / generality evidence
not yet = main H002 compatibility claim
```

## Schema Leakage

Schema leakage check는 통과했다.

```text
model_rows = 1284
hidden_rows = 1284
schema_leakage_passed = true
validation_errors = 0
```

`model_safe_view.jsonl`에는 construction field가 들어가지 않았다. 다음은 hidden manifest에만 있다.

```text
label_match_status
geometry_status
candidate_bucket
distance_bucket
scan_id
directed_pair_id
row_key
prediction_id
p_geom_valid
p_geom_invalid
```

## Critical Blockers

Primary binary target에서 다음 baseline이 target을 거의 완전히 맞춘다.

```text
primary_binary:normalized_distance_xy
  accuracy = 1.000000
  AUROC = 1.000000

primary_binary:normalized_distance_3d
  accuracy = 1.000000
  AUROC = 1.000000

primary_binary:distance_xy
  accuracy = 0.992500
  AUROC = 0.999556

primary_binary:distance_3d
  accuracy = 0.987500
  AUROC = 0.998975

primary_binary:p_geom_valid_rule
  accuracy = 0.991250
  AUROC = 0.999594
```

Raw-distance diagnostic subset에서도 normalized distance가 완전히 맞춘다.

```text
raw_distance_diagnostic:normalized_distance_xy
  accuracy = 1.000000
  AUROC = 1.000000

raw_distance_diagnostic:normalized_distance_3d
  accuracy = 1.000000
  AUROC = 1.000000

raw_distance_diagnostic:p_geom_valid_rule
  accuracy = 0.995833
  AUROC = 0.994097
```

## Interpretation

이 결과는 `close by`가 불필요하다는 뜻이 아니다. 오히려 proximity family는 geometry evidence가
너무 강한 relation이라는 뜻에 가깝다. H002 main claim은 `T_e`와 `G_e` compatibility가 단순한
geometry threshold보다 더 많은 것을 설명해야 하는데, 현재 `close by` target은 그 조건을 만족하지
못한다.

따라서 지금 단계에서의 판단은 다음이다.

```text
learned_smoke_allowed = false
close_by_main_claim_allowed = false
close_by_diagnostic_allowed = true
```

## Next

```text
compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit
```

다음 path decision에서 선택지는 다음 중 하나다.

1. `close by`를 diagnostic/generality evidence로 freeze한다.
2. normalized-distance matched target을 새로 만들 수 있는 다른 candidate source를 찾는다.
3. `close by`는 appendix/failure taxonomy로 두고 support/contact individual predicate probe로 이동한다.
