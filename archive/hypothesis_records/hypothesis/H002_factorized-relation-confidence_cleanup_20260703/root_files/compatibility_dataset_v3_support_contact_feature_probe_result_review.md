# Compatibility Dataset V3 Support/Contact Feature Probe Result Review

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review/
status = h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan
selected_path = select_pose_conditioned_same_geometry_support_contact_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_target_plan
```

## Purpose

This review interprets the completed support/contact mesh-pose-contact feature probe.
The key question is not whether features can be computed. That was already answered by
the previous runner. The key question is whether these features justify moving directly
to candidate materialization or learned smoke.

## Inputs

```text
feature_probe_runner = artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner/
source_inventory = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory/
```

## Feature Availability Result

The availability and derivability blockers are cleared:

```text
support_rows = 161498
tier_a_records = 161498
tier_b_records = 1200
tier_b_distinct_scans = 654
all_reviewed_features_derivable = true
old_numeric_proxy_dominance_high_count = 0
```

Interpretation:

Support/contact can now use real mesh/pose/contact `G_e` candidates rather than only old
distance, gap, and overlap proxies. This is a useful improvement over the previous
numeric-only branch.

## Predicate Contrast Review

```text
lying on vs standing on:
  verdict = pose_conditioned_contrast_candidate
  max_abs_standardized_delta = 0.4384
  max_delta_feature = point_surface_gap_subject_bottom_to_object_top

lying on vs supported by:
  verdict = pose_conditioned_contrast_candidate
  max_abs_standardized_delta = 0.3748
  max_delta_feature = point_surface_gap_subject_bottom_to_object_top

standing on vs supported by:
  verdict = collapse_or_superordinate_overlap
  max_abs_standardized_delta = 0.1398
  max_delta_feature = point_contact_candidate_ratio
```

Interpretation:

- `lying on` has usable pose/contact-distribution differences against upright support predicates.
- `standing on` and `supported by` should not be used as clean opposing labels.
- `supported by` behaves like a superordinate support predicate under the current evidence.
- The next target should focus on pose-conditioned compatibility, not generic support/contact
  presence.

## Remaining Blockers

```text
hard_surface_dominance = high
queue_imbalance = high
same_exact_pair_clean_capacity = 4
standing_supported_as_primary_negative_pair = fail
```

High-risk features:

```text
HL/LH queue shift:
  center_delta_z
  surface_gap_subject_bottom_to_object_top
  xy_overlap_object_ratio

hard-surface shift:
  center_distance_xy
```

These risks mean that direct support/contact materialization would likely recreate a shortcut
target. In particular, HL/LH queue kind is not an independent accept/reject label, and floor/wall
dominance can become an object-category shortcut.

## Decision

```text
target_design_plan_allowed = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
paper_evidence_allowed = false
```

The next step is a target-design plan, not materialization.

## Next Target-Design Direction

The next plan should use pose-conditioned same-geometry predicate flips:

```text
same G_e anchor + T_e = lying on      -> compatible or incompatible
same G_e anchor + T_e = standing on   -> opposite compatibility label
```

Design constraints:

- primary contrast: `lying on` vs `standing on`;
- diagnostic contrast: `lying on` vs `supported by`;
- do not use `standing on` vs `supported by` as the primary binary negative pair;
- select anchors using geometry/pose/contact evidence, not source score, rank, or queue kind;
- cap hard-surface rows and require non-hard-surface cells;
- keep source score, rank, queue kind, geometry status, visible pair, and construction provenance
  out of model inputs;
- run schema/shortcut audit before any learned support/contact smoke.

## Boundary

- train-only result review;
- no validation/test usage;
- no H001 artifact modification;
- no candidate materialization;
- no learned smoke;
- no paper evidence.

## Next

```text
compatibility_dataset_v3_support_contact_pose_conditioned_target_plan
```
