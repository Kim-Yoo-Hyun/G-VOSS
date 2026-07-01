# H002 Route-Specific Target Materialization Plan After Manifest Audit

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit/
status = h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_ready
selected_path = freeze_materialization_waves_select_close_by_geometry_support_route_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan
```

## Purpose

route-specific target manifest consistency audit 이후, 어떤 route root를 어떤 순서로
materialization 계획에 올릴지 정리했다. 이 단계는 실제 row를 생성하지 않고, model도
실행하지 않는다.

## Materialization Waves

| Wave | Routes | Purpose |
| --- | --- | --- |
| `W0_normalize_existing_main_routes` | `R2-R5` | existing main-route artifacts를 route-specific root로 정규화하는 계획 |
| `W1_close_by_geometry_only_route` | `R1 close by` | `geometry_support` target을 첫 concrete route로 연다 |
| `W2_supported_by_decomposition_route` | `R6 supported by` | `accept/relabel/reject/abstain` decomposition route를 다음 후보로 둔다 |
| `W3_attachment_observability_schema_audit` | `R7 attached/hanging/connected` | materialization 전에 `p_obs`/`Q_e` evidence availability를 감사한다 |
| `W4_feasibility_capacity_schema_audits` | `R8-R10` | `leaning`, `cover`, containment capacity/schema audit |
| `W5_boundary_future_manifests` | `R11-R13` | identity/symmetry, semantic/structural, embedded-structure boundary/future |

## Selected First Follow-Up

다음 concrete follow-up은 `close by` geometry-only route다.

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
next_todo = compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan
```

반드시 보존해야 할 점:

- `close by`는 `T_e x G_e` interaction proof가 아니다.
- `close by`는 geometry-only learned/evaluated route다.
- target은 `geometry_support`로 보고한다.
- distance / scale / coverage controls를 반드시 포함한다.

## Next Priority

1. `R1 close by`: geometry_support route plan
2. `R6 supported by`: superordinate support decomposition / relabel / abstain plan
3. `R7 attachment`: observability schema audit

## Boundary

Allowed now:

- route-specific materialization planning
- source-artifact reuse planning
- first concrete follow-up selection

Blocked now:

- actual row materialization
- learned smoke runner
- Docker/paper promotion
- calibrated `p_rel` / `p_obs` claim

## Next

```text
compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan
```
