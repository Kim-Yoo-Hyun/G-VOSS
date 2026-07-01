# H002 Route-Specific Target Manifest Plan After Schema Freeze

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze/
status = h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready
selected_path = freeze_per_route_target_manifests_select_manifest_consistency_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan
```

## Purpose

schema freeze 이후 route-specific target manifest를 작성했다. 이 단계는 새 row를
materialize하지 않고, model을 학습하지 않는다. 각 route별로 다음 항목을 고정했다.

- target axis
- label space
- positive / negative / abstain definition
- model-safe view
- hidden construction manifest
- audit view
- required controls
- artifact root
- promotion priority

## Route Target Manifest

| Route | Relations | Target Axis | Label Space |
| --- | --- | --- | --- |
| geometry-only learned/evaluated | `close by` | `geometry_support` | `geometry_supported`, `geometry_unsupported`, `abstain` |
| predicate-geometry interaction | `higher/lower`, `bigger/smaller`, `left/right/front/behind`, `standing/lying on` | `predicate_geometry_compatibility` | `compatible`, `incompatible`, `abstain` |
| superordinate support decomposition | `supported by` | `accept_relabel_abstain` | `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`, `abstain` |
| observability-aware | `attached to`, `hanging on`, `connected to` | `observability_then_reliability` | `observable_accept`, `observable_reject`, `unobservable_abstain`, `functional_or_topology_uncertain` |
| contact-orientation | `leaning against` | `contact_orientation_feasibility` | `leaning_supported`, `leaning_unsupported`, `abstain` |
| occlusion/coverage | `cover` | `occlusion_coverage_feasibility` | `cover_supported`, `cover_unsupported`, `abstain` |
| containment | `standing in`, `lying in`, `hanging in`, `inside` | `containment_feasibility` | `contained`, `not_contained`, `abstain` |
| identity/symmetry | `same as`, `same symmetry as` | `identity_or_symmetry_compatibility` | `same_or_symmetric`, `not_same_or_not_symmetric`, `abstain` |
| semantic/structural | `part of`, `belonging to` | `semantic_structural_compatibility` | `structurally_supported`, `structurally_unsupported`, `abstain` |
| embedded-structure | `build in` | `embedded_structure_feasibility` | `embedded_supported`, `embedded_unsupported`, `abstain` |

## Promotion Priority

1. current main manifest: `relative_vertical`, `size_relative`, `relative_horizontal`,
   `support_contact`
2. claim/control manifest: `close by`, `supported by`
3. next feasibility manifest: `attached/hanging/connected`, `leaning against`, `cover`,
   containment
4. boundary/future manifest: `same/symmetry`, `part of/belonging to`, `build in`

## Boundary

Allowed now:

- route-specific target manifest planning
- model-safe / hidden-field separation
- per-route controls and artifact-root planning

Blocked now:

- row materialization
- learned smoke runner
- Docker/paper promotion
- calibrated `p_rel` / `p_obs` claim

## Next

다음 단계는 manifest consistency audit이다. 즉, route별 manifest가 서로 모순되지 않는지,
`C_e`에 `Z_e`가 들어가지 않는지, hidden construction field가 model-safe view에 들어가지
않는지, `close by`와 `supported by`의 target semantics가 올바르게 분리됐는지 확인한다.

```text
compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan
```
