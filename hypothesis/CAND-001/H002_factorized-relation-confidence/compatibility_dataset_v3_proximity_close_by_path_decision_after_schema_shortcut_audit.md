# Compatibility Dataset V3 Proximity Close-By Path Decision After Schema Shortcut Audit

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe
selected_path = freeze_close_by_diagnostic_select_support_contact_individual_predicate_probe
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```

## Decision

`close by` current target은 diagnostic/generality evidence로 freeze한다.
현재 target으로 learned smoke는 진행하지 않는다.

이유는 target construction 자체가 실패했기 때문이 아니라, 현재 accept/reject label이
거리 기반 rule로 거의 완전히 풀리기 때문이다. 이 상태에서 transformer, MoE, factorized
energy head 같은 더 강한 결합 모델을 얹으면 H002의 핵심 주장인
`T_e-G_e compatibility`를 검증하는 것이 아니라 `close by` distance threshold를 다시
학습한 결과가 된다.

## Critical Evidence

```text
primary_binary normalized_distance_xy = accuracy 1.000000 / AUROC 1.000000
primary_binary normalized_distance_3d = accuracy 1.000000 / AUROC 1.000000
primary_binary distance_xy = accuracy 0.992500 / AUROC 0.999556
primary_binary distance_3d = accuracy 0.987500 / AUROC 0.998975
primary_binary p_geom_valid_rule = accuracy 0.991250 / AUROC 0.999594
```

Schema leakage는 통과했다. 문제는 schema field 누출이 아니라 target이
`distance_only`와 `p_geom_valid_rule`로 충분히 설명된다는 점이다.

## Route Decision

| Route | Verdict | Reason |
| --- | --- | --- |
| current close-by learned smoke | reject | distance/rule geometry baseline이 이미 target을 해결한다 |
| stronger combiner / neural architecture | reject for now | target identifiability가 없는 상태에서는 더 강한 모델이 shortcut을 학습한다 |
| current close-by main H002 claim | reject | proximity threshold 검증이지 compatibility learning 검증이 아니다 |
| stricter close-by source search | defer | 가능하지만 현재 evidence상 우선순위가 낮다 |
| support/contact individual predicate probe | select | distance만으로 끝나지 않는 contact/support geometry evidence를 검토할 수 있다 |

## Next Probe Priority

| Priority | Predicate | Role | Queue Rows | Exact Matches | Note |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `standing on` | primary individual probe | 50245 | 5871 | exact count와 class-pair mixing이 가장 좋지만 floor/table/surface shortcut 통제가 필요하다 |
| 2 | `lying on` | secondary pose-conditioned probe | 60652 | 1440 | pose-conditioned `C_e` mechanism 확인에 유리하다 |
| 3 | `supported by` | diagnostic superordinate probe | 50601 | 491 | superordinate support relation이라 main target보다는 boundary evidence에 가깝다 |

## Claim Boundary

- Train-only path decision이다.
- validation/test는 사용하지 않았다.
- 새 label, row materialization, learned smoke, model training은 진행하지 않았다.
- H001 artifact는 수정하지 않았다.
- `close by`는 H002 generality/failure taxonomy에는 포함하지만, 현재 main learned target으로는 쓰지 않는다.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_probe_plan
```
