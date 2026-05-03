# Evidence Schema

Last updated: 2026-05-03

## Role

This file defines the relation-edge evidence schema used by the H001 smoke tests.

Implementation details live in `tools/`; run results live in `artifacts/`.

## Edge Record

Each relation edge should preserve the original tuple and add inspectable geometry fields:

```text
edge_id
scan_id
subject_id
object_id
subject_label
object_label
predicate_label
predicate_family
geometry_source
geometry_available
object_geometry
geometry_evidence
rule_inputs
missing_fields
notes
```

## Predicate Families

| Family | Labels | Evidence needed |
| --- | --- | --- |
| `support_contact` | `standing on`, `lying on`, `supported by` | vertical order, local support surface, footprint/contact evidence |
| `proximity` | `close by` | normalized XY distance |
| `relative_vertical` | `higher than`, `lower than` | signed z difference |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | coordinate-frame validated x/y relation |
| `attachment_deferred` | `attached to`, `hanging on`, `leaning against`, `connected to` | surface contact and orientation |
| `size_comparison_deferred` | `bigger than`, `smaller than` | object size/volume |
| `unsupported_first_pass` | semantic/appearance/common-sense labels | not geometry-checkable in first pass |

## OBB Evidence

Source:

```text
semseg.v2.json obb
```

Derived fields:

```text
center_xyz
axes_lengths
aabb_min_xyz
aabb_max_xyz
size_xyz
height_z
diag_3d
diag_xy
```

Edge evidence:

```text
delta_xyz
distance_3d
distance_xy
normalized_distance_xy
center_delta_z
normalized_center_delta_z
projected_subject_overlap_ratio
projected_object_overlap_ratio
vertical_gap_subject_on_object
```

Use:

- good enough for first proximity checks;
- usable for relative vertical ordering;
- too coarse for support/contact surfaces.

## Point Evidence

Source:

```text
labels.instances.annotated.v2.ply
```

Required point fields:

```text
x
y
z
objectId
```

For support/contact, compute:

```text
subject robust XY footprint
support points under/near subject footprint
support local z percentiles
subject bottom z percentile
local vertical gap
support point count
```

Use:

- recover support/contact cases that OBB-only evidence marks as uncertain or violated;
- keep sparse or borderline cases as uncertain.

## Subtype Evidence

`h001-verifier-v2` adds subtype-specific support/contact evidence.

Required subtype fields:

```text
support_subtype
consistency_score
score_components
geometry_quality_flags
```

Subtype-specific evidence:

| Subtype | Evidence |
| --- | --- |
| `legged_floor_support` | low-percentile gap, robust gap, support density, contact fraction |
| `soft_support_contact` | signed gap, penetration depth, soft prior, support density |
| `rigid_object_on_furniture` | local horizontal plane, plane residual, plane gap, plane confidence |
| `geometry_quality_uncertain` | visual ambiguity, point density, instance completeness flags |

## Missing Data Policy

- Preserve every edge.
- Mark missing geometry as `uncertain`, not false.
- Mark unsupported predicates as unsupported, not false.
- Keep counts by predicate family for reporting.

## Current Evidence Sources

| Source | Version | Status |
| --- | --- | --- |
| OBB-derived AABB | `semseg_obb_v0` | implemented |
| rule verifier | `h001-rules-v0` | implemented |
| point/local support evidence | `ply_points_v1` | implemented |
| point-aware verifier | `h001-rules-v1` | implemented |
| subtype-aware verifier | `h001-verifier-v2` | implemented |
| calibration design | `15_calibration.md` | written |
| evaluation protocol | `16_evaluation.md` | written |
| official subset strategy | `17_subset.md` | written |
| baseline decision | `18_baseline.md` | written |
| prediction schema | `19_schema.md` | written |
| layout compatibility | `20_layout.md` | checked |
| layout checker | `tools/check_layout.py` / `artifacts/layout/vlsat/` | implemented |
| eval path | `21_eval_path.md` | faithful route decided |
| prep policy | `22_prep.md` | written |
| H001-Mini selection | `23_mini.md` / `artifacts/subset/h001_mini/` | fixed |

## Open Decisions

- how to export a calibration table without leaking scan-specific labels;
- whether proximity threshold should be calibrated on more scans;
- whether horizontal relations should be promoted after coordinate-frame validation.
