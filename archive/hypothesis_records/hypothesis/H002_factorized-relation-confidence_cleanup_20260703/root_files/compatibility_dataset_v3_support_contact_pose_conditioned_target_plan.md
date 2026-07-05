# Compatibility Dataset V3 Support/Contact Pose-Conditioned Target Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan
selected_path = capacity_scan_pose_conditioned_same_geometry_lying_standing_target
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan
```

## Purpose

This plan defines the next support/contact target after the mesh/pose/contact feature probe.
It does not materialize rows and does not train a model. Its role is to freeze a target design
that can be capacity-scanned safely.

## Core Target

Primary contrast:

```text
same G_e anchor + T_e = lying on
same G_e anchor + T_e = standing on
```

The target uses two rows per anchor. The geometry evidence `G_e` is shared, while the predicate
semantic content `T_e` changes.

Label policy:

```text
lying-like support/contact pose:
  lying on = positive
  standing on = negative

upright support/contact pose:
  standing on = positive
  lying on = negative
```

This preserves the H002 compatibility claim: geometry alone should not solve the row label,
and predicate alone should not solve it either. The useful signal should come from
`compatibility(T_e, G_e)`.

## Role of Supported By

`supported by` is not used as the primary negative for `standing on`.

Reason:

```text
standing on vs supported by = collapse_or_superordinate_overlap
```

The previous result review showed that `supported by` behaves like a superordinate support
predicate under the current evidence. It can be kept as a diagnostic or superordinate label, but
not as a clean binary opposite to `standing on`.

## Anchor Policy

The capacity scan must find anchors that pass support/contact evidence first, then classify the
pose state:

```text
contact/support core:
  abs surface gap
  XY overlap / support area
  point contact candidate ratio

lying pose:
  low / flat subject geometry
  low subject vertical extent
  non-vertical dominant axis

upright pose:
  high subject vertical extent
  vertical dominant axis
  sufficient bottom-band support density
```

Ambiguous pose, weak contact, low point coverage, or hard-surface ambiguous rows should become
abstain or diagnostic rows, not forced negatives.

## Quota Gate

The capacity scan should check whether the following target is feasible:

```text
target_anchor_groups = 200
minimum_anchor_groups = 120
target_total_rows = 400
minimum_total_rows = 240
minimum_lying_like_anchors = 60
minimum_upright_anchors = 60
minimum_non_hard_surface_share = 0.30
max_single_visible_pair_share = 0.12
max_single_scan_share = 0.10
```

Each anchor group must contain two rows:

```text
same G_e, predicate = lying on
same G_e, predicate = standing on
```

## Blocked Inputs

The following fields remain audit/control only:

```text
anchor_pose_state
queue_kind
geometry_status
source_score
source_rank
rank_band
visible_pair
scan_id
subject_instance_id
object_instance_id
p_geom_valid
consistency_score
disagreement_score
underconfidence_score
counterfactual_type
row_role
human_label
```

## Planned Baselines And Controls

The later smoke, if materialization passes, must include:

- source-only `Z_e`;
- semantic-only `T_e`;
- geometry-only `G_e`;
- plain `T_e + G_e`;
- predicate-conditioned compatibility interaction;
- wrong-`T_e` same-`G_e` control;
- shuffled-`G_e` same-predicate control;
- hard-surface-only audit probe.

Expected behavior:

```text
source-only ~= chance
semantic-only ~= chance
geometry-only ~= chance
compatibility interaction > baselines
wrong-T and shuffled-G controls degrade
```

## Decision

```text
capacity_scan_allowed = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
paper_evidence_allowed = false
```

## Boundary

- train-only target design plan;
- no validation/test usage;
- no H001 artifact modification;
- no candidate materialization;
- no learned smoke;
- no paper evidence.

## Next

```text
compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan
```
