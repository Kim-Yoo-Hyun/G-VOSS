# H002 Support/Contact Individual Predicate Point/Multiview Evidence Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan_ready_for_source_inventory
selected_path = g_q_separated_audit_first_point_multiview_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory
```

## Why This Plan Exists

The OBB-only individual-predicate smoke produced a real but weak interaction signal:

```text
M4 interaction AUROC = 0.631611328125
geometry-only AUROC = 0.5092333984375
semantic-only AUROC = 0.410830078125
errors = 267
false_positive / false_negative = 144 / 123
```

The conclusion is not to add a stronger combiner first. The bottleneck is that
semseg OBB geometry does not expose enough point/contact/pose/observability evidence
for `standing on` versus `lying on`.

## Factor Boundary

The next branch must keep `G_e` and `Q_e` separate:

- `G_e`: predicate-independent geometry evidence from point/mesh/contact/pose.
- `Q_e`: whether that evidence is sufficient to decide.
- multiview crops: audit and `Q_e` support first, not immediate learned visual input.
- `T_e`: predicate/object semantic content only.
- `Z_e`: source confidence only, excluded from `C_e`.

This is important because adding point or visual evidence can make the model stronger
while also introducing new shortcuts. The immediate stage therefore plans source
inventory and factor-safe materialization, not a visual encoder or stronger classifier.

## Relation-Specific Routes

```text
standing on  -> upright pose + bottom contact + support surface below
lying on     -> horizontal pose + broad or elongated contact
supported by -> broad support/superordinate diagnostic, not main binary target
```

`supported by` remains diagnostic-only because it is a broad support relation and can
collapse the subtype boundary between `standing on` and `lying on`.

## Asset Readiness

The current 800 train-only candidate rows have the required source assets available:

```text
candidate_rows = 800
main rows = 640
diagnostic rows = 160
unique_scans = 357
point_ready_rows = 800
mesh_ready_rows = 800
multiview_ready_rows = 800
all_ready_rows = 800
missing_asset_rows = 0
```

Per predicate:

```text
standing on = 320 / 320 all-ready
lying on = 320 / 320 all-ready
supported by = 160 / 160 all-ready
```

## Required Evidence

`standing on`:

- subject uprightness;
- bottom contact band;
- support surface below;
- support normal verticality;
- local point/mesh contact patch.

`lying on`:

- subject horizontalness;
- major-axis pose;
- broad or elongated contact area;
- support surface overlap;
- low vertical extent ratio.

`Q_e`:

- point density near contact bands;
- mesh/semseg completeness;
- contact patch point count;
- co-visible view count;
- pair crop quality;
- occlusion/conflict/missing flags.

## Controls

Before learned smoke, the next source inventory/materialization must preserve:

- hidden-only construction fields: `label_match_status`, `candidate_role`, `queue_kind`,
  `machine_hint`, GT ids;
- class-pair/rank/source controls;
- OBB-only vs point-only vs point+mesh comparisons;
- wrong-pair geometry and shuffled geometry controls;
- wrong-view and shuffled-view controls before any visual feature enters model input.

## Promotion Gates

The support/contact individual predicate branch cannot become a main H002 claim unless:

```text
source_inventory_ready >= 95%
Q_e has non-constant sufficient / limited / missing-or-conflict states
G_e contains no predicate/source/label fields
T_e + G_e or C_e AUROC >= 0.70 under grouped CV
corruption controls degrade clearly
```

## Decision

Selected path:

```text
g_q_separated_audit_first_point_multiview_source_inventory
```

Meaning:

- keep the current OBB-only result diagnostic;
- do not lower the `0.70` gate;
- do not add visual encoder features yet;
- first run point/multiview source inventory;
- then materialize `G_e` and `Q_e` separately;
- keep `supported by` diagnostic-only until the subtype boundary is clearer.

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory
```
