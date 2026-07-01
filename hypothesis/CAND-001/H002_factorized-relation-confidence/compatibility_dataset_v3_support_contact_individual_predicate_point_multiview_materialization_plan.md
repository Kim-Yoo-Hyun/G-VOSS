# H002 Support/Contact Individual Predicate Point/Multiview Materialization Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_ready
selected_path = plan_gq_separated_materialization_with_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization
```

## Planned Scope

```text
rows = 800
main_rows = 640
diagnostic_rows = 160
standing on = 320
lying on = 320
supported by = 160
Q_e states = limited 419 / sufficient 373 / uncertain_or_low_observability 8
```

`standing on` and `lying on` are the primary materialization scope. `supported by` is
materialized for diagnostic analysis but is excluded from primary smoke.

## Feature Blocks

The next materialization must emit separate factor blocks:

```text
T_e
G_e_obb_baseline
G_e_point_pose
G_e_contact_patch
Q_e_observability
V_mv_audit_manifest
Z_e_safe
```

`G_e_obb_baseline` keeps the current OBB-only evidence for ablation. `G_e_point_pose`
and `G_e_contact_patch` are the new geometry evidence blocks. `Q_e_observability`
stores evidence sufficiency, not relation truth. `V_mv_audit_manifest` is audit and
`Q_e` metadata only, not learned visual input.

## Model Views

Planned model views after materialization:

```text
T_only
G_obb_only
G_point_pose_only
G_contact_patch_only
G_point_mesh_full
T_plus_G_point_mesh
T_plus_G_plus_Q
Z_plus_C_plus_Q_later
```

The main compatibility view is:

```text
T_plus_G_point_mesh = T_e + G_e_point_pose + G_e_contact_patch
```

`Z_plus_C_plus_Q_later` is reserved for later `p_rel/p_obs` decision work and must not
enter the immediate `C_e` compatibility head.

## Required Controls

The materialized artifact must support:

- OBB-only baseline;
- point-only ablation;
- mesh/contact-only ablation;
- wrong-pair geometry;
- shuffled geometry, global;
- shuffled geometry, within predicate;
- wrong-view control;
- shuffled-view control;
- class-pair/rank/source shortcut probe.

The view controls are defined now even though learned visual input remains blocked. This
prevents visual evidence from becoming an untested shortcut later.

## Blocked Fields

The model-safe artifact must not include:

- scan/source paths;
- scan id, subgraph id, subject id, object id;
- candidate role;
- `label_match_status`;
- queue kind;
- machine hint;
- GT ids or matched GT predicates;
- construction geometry status;
- H001 `p_geom_valid` as a `C_e` input;
- source score or rank inside `C_e`;
- audit accept/reject labels;
- learned visual embeddings.

## Planned Outputs

```text
model_safe_view.jsonl
source_manifest.jsonl
visual_audit_manifest.jsonl
control_manifest.jsonl
feature_stats.json
validation_errors.jsonl
```

The `model_safe_view.jsonl` should contain only factor-separated safe fields. The
source and visual manifests are hidden/provenance or audit artifacts.

## Decision

Selected path:

```text
plan_gq_separated_materialization_with_controls
```

Meaning:

- proceed to actual materialization;
- do not run learned smoke yet;
- do not use validation/test rows;
- do not write H001 artifacts;
- do not use multiview learned embeddings;
- keep multiview audit/`Q_e` first;
- keep `supported by` diagnostic-only.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization
```
