# Compatibility Dataset V3 Independent Validity Support Contact Balancing Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan/
status = h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_ready_for_materialization
selected_path = materialize_support_contact_primary_independent_validity_with_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization
```

## Purpose

직전 independent-validity smoke는 전체적으로 `C_e = compatibility(T_e, G_e)`의 강한
증거를 보였지만, `support_contact_pose_conditioned`가 `88 / 1600` rows뿐이라 primary
family generality를 주장할 수 없었다.

이번 단계는 support/contact를 별도 primary independent-validity target으로 만들 수 있는지
검토하고, 다음 materialization contract를 고정한다.

## Capacity Diagnosis

현재 exact predicate-class balance를 그대로 쓰면 support/contact는 너무 작다.

```text
current exact predicate-class support/contact rows = 88
lying on exact rows = 64
standing on exact rows = 24
```

하지만 predicate-level independent-validity capacity는 충분하다.

```text
support/contact family scan-capped capacity = 2134
lying on scan-capped capacity = 1370
standing on scan-capped capacity = 764
```

따라서 문제는 support/contact 자체의 data 부족이 아니라, exact predicate-class balance가
support/contact에는 너무 강한 constraint라는 점이다.

## Selected Route

선택한 route:

```text
predicate_balanced_support_contact_independent_validity
```

Materialization target:

```text
target rows = 1200
minimum rows = 800
lying on = 600 rows
standing on = 600 rows
positive / negative per predicate = 300 / 300
```

Positive policy:

```text
label_match_status = exact_match
geometry_status = satisfied
```

Negative policy:

```text
label_match_status in {family_match, pair_has_other_predicate}
geometry_status = unsatisfied
```

Primary에서 제외:

```text
no_gt_for_pair
gt_conflict_exact_unsatisfied
geometry_uncertain
geometry_unsupported
```

## Why Not Other Routes

- Exact predicate-class balance: shortcut control은 강하지만 support/contact가 `88` rows에 갇혀 primary target이 될 수 없다.
- Pose-conditioned constructed target: `400` rows와 clean controls는 있지만 constructed `C_e` label이라 independent-validity GT가 아니다.
- Larger architecture: support/contact-primary model-safe dataset이 없어서 아직 이르다.
- Calibrated `p_rel`: held-out reliability target과 selective-decision protocol이 없어서 아직 claim할 수 없다.

## Controls Required Next

다음 materializer는 predicate-level balance를 쓰는 대신 아래 controls를 강하게 걸어야 한다.

- max single scan share: `0.05`
- max single directed pair share: `0.01`
- max single subject/object class pair share: `0.10`
- max single rank band share: `0.55`
- class-pair distribution audit
- rank-band distribution audit
- schema shortcut audit before learned smoke

Model input에서 계속 막을 필드:

```text
geometry_status
p_geom_valid
consistency_score
geometry_residual_proxy
label_match_status
matched_gt_ids
matched_predicates
target_pool
selection_pass
hidden provenance
```

## Claim Boundary

Allowed now:

- train-only support/contact-primary independent-validity materialization plan
- support/contact family balancing route decision
- constructed pose-conditioned target as auxiliary `C_e` mechanism evidence only

Blocked:

- calibrated `p_rel` / `p_obs`
- paper-level H002 result
- held-out performance
- all-family 3DSSG relation reliability
- learned smoke before candidate materialization and schema shortcut audit

## Next

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization
```
