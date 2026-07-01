# H002 Route-Coverage Sufficiency Review After Relative-Horizontal Table Plan

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan/
status = h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready
selected_path = coverage_sufficient_for_hypothesis_framework_proceed_to_schema_freeze_promotion_protocol_no_new_family_now
validation_errors = 0
next_todo = compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review
```

## Decision

현재 route coverage는 H002의 hypothesis-stage framework claim에는 충분하다고
판정했다. 따라서 다음 단계에서 새로운 relation family를 추가로 mining하지 않고,
schema freeze와 promotion protocol을 먼저 작성한다.

핵심 이유:

- `relative_vertical`: clean signed geometry compatibility anchor
- `size_relative`: clean non-axis physical compatibility anchor
- `relative_horizontal`: reference-frame-aware directional compatibility route
- `support_contact`: challenging contact/pose compatibility route with caveat
- `proximity`: geometry-easy control / diagnostic route
- `attachment_like`: observability-heavy future/deferred boundary
- `supported by`, `containment`, `part/structural`, `identity/symmetry`: diagnostic,
  future, or out-of-scope boundary

## Interpretation

이 결론은 “모든 3DSSG/Open3DSG relation family를 다룬다”는 의미가 아니다.
현재 허용되는 claim은 다음과 같이 제한된다.

```text
Relation-aware predicate-geometry compatibility routing can be studied with
clean, frame-aware, challenging, diagnostic, and deferred evidence routes.
```

즉, H002가 바로 paper-level reliability result로 승격된 것은 아니다. 이번 단계는
relation family discovery를 일단 멈추고, 현재 route set으로 promotion protocol을
작성할 수 있는지를 결정한 gate다.

## Blocked Claims

아래 claim은 여전히 금지된다.

- all-family generality
- calibrated `p_rel` / `p_obs`
- held-out/test reliability
- paper-level performance
- complete horizontal ontology including `in front of`
- support/contact fully solved
- geometry-only framework

## Next

다음 단계는 schema freeze와 promotion protocol이다.

```text
compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review
```
