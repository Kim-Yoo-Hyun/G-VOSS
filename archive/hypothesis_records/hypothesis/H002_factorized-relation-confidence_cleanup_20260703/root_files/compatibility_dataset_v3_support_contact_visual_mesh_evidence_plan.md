# Compatibility Dataset V3 Support/Contact Visual-Mesh Evidence Plan

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_ready
selected_route = mesh_pose_contact_first_multiview_audit_first
next = compatibility_dataset_v3_support_contact_visual_mesh_source_inventory
validation_errors = 0
```

## Purpose

직전 evidence probe에서 `support_contact` numeric-only smoke는 막혔다. 이유는 row 수가
부족해서가 아니라, 현재 numeric `G_e`가 `distance`, `overlap`, `vertical gap`, OBB
top/bottom 위주라서 `standing on`, `lying on`, `supported by`의 predicate-conditioned
compatibility를 검증하기 어렵기 때문이다.

이 plan은 다음 방향을 고정한다.

```text
numeric-only support/contact smoke = blocked
mesh / pose / contact evidence = primary next G_e candidate
multi-view evidence = audit / Q_e first, model input later
attachment packet assets = renderer/template reference only
```

## Source Snapshot

Generated artifact:

```text
artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan/
```

Current source availability:

```text
3RScan scan dirs = 1335
mesh refined obj = 1335
aligned instance ply = 1335
sequence.zip = 1335
visual contact sheets = 192
visual support/contact sheets = 64
attachment packet template dirs = 560
```

Interpretation:

The raw sources likely contain the evidence axis we need, but the evidence is not yet joined to
support/contact candidate rows. Therefore this is not evidence that support/contact is ready for
learned smoke. It only justifies the next source-inventory step.

## Evidence Axis Plan

Primary `G_e` candidates:

- `mesh_instance_points`: pair point crop, instance PCA axes, extents, support candidate surface
  bands;
- `mesh_contact_surface`: surface gap histogram, contact patch area, support overlap, local
  surface normal alignment;
- `role_orientation_pose`: uprightness, horizontalness, major-axis alignment, bottom-contact band.

Secondary `Q_e` / audit-first candidates:

- `multi_view_covisibility`: co-visible frame count, subject/object visibility, pair crop quality,
  occlusion/conflict flags;
- `reviewer_packet_visuals`: reviewer-visible packet for independent accept/reject/abstain label
  confirmation.

Control-only evidence:

- current numeric OBB/distance/overlap features remain baselines and shortcut-risk checks.

## Relation-Family Mapping

| Predicate | Required evidence | Main hard negative |
| --- | --- | --- |
| `standing on` | support contact plus upright subject pose | same support proximity but subject not upright or no support contact |
| `lying on` | support contact plus horizontal subject pose | same support contact but upright or only nearby |
| `supported by` | support direction and stable surface relation | near or overlapping without upward support |

This is why the next step should prioritize mesh/pose/contact features before making multi-view a
deployable model feature. Multi-view is useful, but if used too early it can make the method look
like "extra visual feature + target shortcut" rather than a principled `C_e` extension.

## Factor Boundary

```text
T_e = predicate/class semantic content
Z_e = source confidence/rank
G_e = predicate-independent mesh/pose/contact geometry evidence
C_e = compatibility(T_e, G_e)
Q_e = evidence availability / observability / uncertainty
```

Rules:

- `Z_e` must not enter `C_e`;
- human audit labels must not become model features;
- hidden construction fields such as counterfactual type or row role stay audit-only;
- multi-view can be used for `Q_e` and audit labels first;
- deployable visual features require a later shortcut-controlled source inventory and materializer.

## Route Decision

Selected:

```text
mesh_pose_contact_first_multiview_audit_first
```

Rejected or deferred:

- run numeric-only support/contact smoke now;
- reuse attachment packet labels as support/contact labels;
- add multi-view directly as model input before source inventory and controls;
- promote support/contact generality from v2 generated negatives.

## Next Runner Contract

```text
next = compatibility_dataset_v3_support_contact_visual_mesh_source_inventory
```

The next runner should output:

- `scan_asset_inventory.csv`;
- `support_contact_candidate_source_join_preview.jsonl`;
- `mesh_pose_contact_feature_feasibility.csv`;
- `multiview_packet_feasibility.csv`;
- `shortcut_and_scope_risk.csv`;
- `path_decision.json`;
- `summary.json`;
- `report.md`.

Success condition:

the source-inventory runner must show that support/contact train candidates can be joined to
mesh, instance labels, sequence frames, or packet-rendering assets without exposing source score,
construction proxy, human labels, or validation/test information.

## Boundary

- Train-only plan.
- No candidate materialization.
- No learned smoke.
- No validation/test usage.
- No paper-level evidence promotion.
- No H001 artifact modification.
