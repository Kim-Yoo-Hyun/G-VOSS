# H002 Schema Freeze And Promotion Protocol After Route-Coverage Review

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review/
status = h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready
selected_path = freeze_route_specific_target_definitions_and_promotion_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze
```

## Core Decision

H002의 target 정의를 relation별로 다시 고정했다. 이제 H002는 어떤 relation이
learned compatibility target인지 아닌지를 나누지 않는다. 핵심은 각 relation family가
어떤 evidence route와 target semantics를 요구하는지 식별하는 것이다.

Frozen claim:

```text
H002 asks which evidence route and target definition each relation family requires:
geometry-only, predicate-geometry interaction, observability-aware, superordinate
decomposition, identity/symmetry, or semantic/structural.
```

## Frozen Route Taxonomy

| Route | Relations | Role |
| --- | --- | --- |
| geometry-only learned/evaluated route | `close by` | claim/control evidence |
| predicate-geometry interaction route | `higher than`, `lower than`, `bigger than`, `smaller than`, `left`, `right`, `front`, `behind`, `standing on`, `lying on` | main mechanism evidence |
| superordinate support decomposition / relabel / abstain route | `supported by` | claim/control or next probe |
| observability-aware route | `attached to`, `hanging on`, `connected to` | next probe / future evidence |
| contact-orientation route | `leaning against` | next feasibility route |
| occlusion/coverage route | `cover` | next feasibility route |
| containment route | `standing in`, `lying in`, `hanging in`, `inside` | next feasibility route |
| identity/symmetry route | `same as`, `same symmetry as` | separate task candidate |
| semantic/structural route | `part of`, `belonging to` | semantic-structural boundary or future |
| embedded-structure route | `build in` | future feasibility route |

## Main Mechanism Rows

The current main `T_e x G_e` mechanism rows remain:

```text
higher than / lower than
bigger than / smaller than
left / right / front / behind
standing on / lying on
```

`close by` is no longer described as merely diagnostic. It is frozen as a
geometry-only learned/evaluated route. `supported by` is not a clean binary target;
it is a superordinate support decomposition / relabel / abstain route.

## Promotion Boundary

Allowed now:

- route-specific target definition
- train-only framework claim
- geometry-only route for `close by`
- predicate-geometry route for the current main mechanism rows
- observability, decomposition, identity/symmetry, and semantic/structural routes as
  protocol/future/boundary routes

Blocked now:

- paper-level reliability improvement
- calibrated `p_rel` / `p_obs`
- all relation types using the same target definition
- all-family solved/general relation reliability
- forcing all relation types into one binary target or one fixed fusion head

## Next

다음 단계는 route-specific target manifest plan이다. 즉, 각 route별로 model-safe view,
hidden construction fields, positive/negative/abstain definition, controls, and artifact
roots를 명시한다.

```text
compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze
```
