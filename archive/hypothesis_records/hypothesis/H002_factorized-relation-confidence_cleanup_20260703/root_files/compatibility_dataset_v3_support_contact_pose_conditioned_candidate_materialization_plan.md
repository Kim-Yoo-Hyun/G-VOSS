# Compatibility Dataset V3 Support/Contact Pose-Conditioned Candidate Materialization Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_ready
selected_path = materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization
```

## Purpose

This plan freezes the exact materialization policy for the support/contact pose-conditioned target.
It does not create candidate rows and does not run learned smoke.

The next materializer must reuse the frozen capacity preview exactly:

```text
source = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan/anchor_candidate_preview.jsonl
anchors = 200
rows_per_anchor = 2
expected_rows = 400
```

## Materialization Rule

Each frozen anchor becomes two rows with the same `G_e` and different `T_e`:

```text
same G_e + predicate = lying on
same G_e + predicate = standing on
```

Label rule:

```text
lying_like_support_contact:
  lying on = 1
  standing on = 0

upright_support_contact:
  lying on = 0
  standing on = 1
```

Expected materialized counts:

```text
anchor_groups = 200
candidate_rows = 400
positive_rows = 200
negative_rows = 200
lying_on_rows = 200
standing_on_rows = 200
lying_like_anchors = 100
upright_anchors = 100
```

## Allowed Actions

The materializer may:

- read the frozen 200-anchor preview;
- expand each anchor into `lying on` and `standing on` rows;
- copy model-safe `T_e`, `G_e`, `Q_e`, and `Z_e_safe` availability fields;
- create audit-only hidden controls;
- write `candidate_rows.jsonl`, `smoke_ready_candidate_view.jsonl`, `hidden_manifest.jsonl`,
  manifest, summary, report, and validation errors.

## Forbidden Actions

The materializer must not:

- select additional anchors;
- change thresholds;
- refill rows after selection;
- use queue kind as a target label;
- use source score/rank in the compatibility label;
- materialize validation/test rows;
- run learned smoke.

## Blocked Model Inputs

The following fields are audit-only and must not enter the model-safe view:

```text
anchor_pose_state
queue_kind
geometry_status
source_score
semantic_rank
rank_band
visible_pair
scan_id
subject_id
object_id
p_geom_valid
consistency_score
disagreement_score
underconfidence_score
target_rows_preview
compatibility_y
```

`compatibility_y` is the target, not an input.

## Required Post-Materialization Gates

The next materialization output must pass:

- row-count integrity;
- label balance;
- same-`G_e` pair integrity;
- blocked-field absence from model-safe view;
- shortcut precheck;
- grouped-CV contract with `anchor_id` as group.

Learned smoke remains blocked until schema/shortcut audit passes.

## Decision

```text
candidate_materialization_allowed = true
learned_smoke_allowed = false
paper_evidence_allowed = false
```

## Boundary

- train-only materialization plan;
- no validation/test usage;
- no H001 artifact modification;
- no candidate row materialization in this step;
- no learned smoke;
- no paper evidence.

## Next

```text
compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization
```
