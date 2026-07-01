# H002 R1 Close-By Geometry-Support Materialization Plan After Route Plan

Date: 2026-06-30 KST

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan/
status = h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_ready
selected_path = materialize_r1_close_by_as_geometry_support_route_root_not_interaction_claim
validation_errors = 0
next_todo = compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan
```

## Purpose

This step writes the concrete R1 `close by` route materialization plan. It does
not materialize rows and does not run a model.

The important change is interpretive: previous `close by` shortcut findings are
not promoted into predicate-geometry interaction evidence. They are reframed as
expected behavior for a geometry-only route.

## Planned Route

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
route_type = geometry_only_learned_evaluated_route
planned_route_root = artifacts/route_specific_targets/r1_proximity/
```

## Row Material To Reuse

| Component | Rows | Use |
| --- | ---: | --- |
| primary geometry-support binary | 800 | `geometry_supported` vs `geometry_unsupported` |
| Q_e / abstain diagnostics | 240 | coverage, ambiguity, or missing/uncertain geometry |
| raw-distance diagnostic | 240 | raw-vs-normalized distance and scale control |
| GT/geometry conflict audit | 4 | audit only, not training |

## Field Contract

- `T_e`: annotation/baseline only for this route.
- `Z_e`: source baseline only; not allowed to define `geometry_support`.
- `G_e`: primary route evidence.
- `Q_e`: abstain/coverage evidence; not relation truth.
- `C_e`: predicate-geometry interaction is `not_applicable` for R1.

## Required Controls

- distance and normalized-distance baseline
- raw-distance vs scale-normalized distance comparison
- coverage / ambiguity / missing-geometry abstain split
- source score and rank-only baseline
- class-pair and endpoint leakage audit
- shuffled-G and wrong-pair geometry controls
- wording guard: R1 is geometry-only route evidence

## Boundary

- Train-only planning artifact.
- No validation/test used.
- No H001 artifact modified.
- No row materialization yet.
- No learned smoke or paper-level result claim.
- `close by` must not be described as `T_e x G_e` interaction evidence.

## Next

```text
compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan
```
