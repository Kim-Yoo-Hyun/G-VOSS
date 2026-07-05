# H002 Support/Contact Individual Predicate Point/Multiview Source Inventory

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_ready_for_materialization_plan
selected_path = source_inventory_ready_for_gq_separated_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan
```

## Inventory Result

The current 800 train-only support/contact individual predicate candidates are source-ready:

```text
rows = 800
unique_scans = 357
point_pair_crop_possible = 800 / 800
mesh_contact_patch_possible = 800 / 800
multiview_packet_possible = 800 / 800
g_e_point_mesh_ready = 800 / 800
```

This means the branch can proceed to a `G_e` / `Q_e` separated materialization plan.
It does not mean learned visual features are allowed yet.

## Q_e State Plan

The previous OBB-only smoke had constant `Q_e`:

```text
mesh=True | point=False | view=False = 640 / 640
```

The new source inventory can create non-constant `Q_e` states:

```text
limited = 419
sufficient = 373
uncertain_or_low_observability = 8
```

Main reasons:

```text
low_semseg_segment_count = 345
low_crop_score = 98
few_cropped_instance_views = 60
```

Per predicate:

```text
standing on: limited 182 / sufficient 134 / uncertain 4
lying on:    limited 170 / sufficient 146 / uncertain 4
supported by: limited 67 / sufficient 93
```

## Factor Boundary

The next materialization must keep the factor boundary:

- `G_e`: point/mesh/contact/pose evidence only.
- `Q_e`: source sufficiency, crop quality, view count, point/mesh completeness, and conflict/missing flags.
- `T_e`: predicate/object semantic content.
- `Z_e`: source confidence/rank only.
- visual/multiview crop: audit and `Q_e` support first, not learned visual input.

Forbidden model-input leakage:

- GT match status;
- candidate role;
- source queue kind;
- machine hint;
- scan/source path;
- audit accept/reject label;
- source rank inside `C_e`.

## Materialization Contract

Next materialization should derive:

- point-pair crop metadata;
- local contact patch numeric features;
- point-based pose/orientation features;
- local support surface statistics;
- point crop density and mesh contact availability;
- multiview crop count and co-visible view count;
- crop quality score/ratio proxies;
- occlusion/conflict/missing-source flags.

Controls required after materialization:

- OBB-only vs point/mesh feature comparison;
- point-only and mesh/contact-only ablation;
- wrong-pair geometry;
- shuffled geometry within predicate;
- wrong-view control before visual input;
- shuffled-view control before visual input;
- class-pair/rank/source shortcut audit.

## Decision

Selected path:

```text
source_inventory_ready_for_gq_separated_materialization_plan
```

Meaning:

- proceed to materialization planning;
- do not run learned smoke yet;
- do not train a visual encoder yet;
- keep `supported by` diagnostic-only;
- materialize `G_e` and `Q_e` separately before any posterior or stronger combiner.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan
```
