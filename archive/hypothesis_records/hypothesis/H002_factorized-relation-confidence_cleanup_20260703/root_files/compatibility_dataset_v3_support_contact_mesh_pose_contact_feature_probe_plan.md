# Compatibility Dataset V3 Support/Contact Mesh-Pose-Contact Feature Probe Plan

## Status

```text
status = h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_ready
selected_route = semseg_obb_normal_full_probe_ply_contact_sample_probe
next = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner
validation_errors = 0
```

## Purpose

이 단계는 source inventory에서 join 가능성이 확인된 support/contact 후보에 대해 어떤
mesh/pose/contact `G_e` 후보를 계산하고 검증할지 고정하는 plan이다. 아직 candidate
materialization, target construction, learned smoke는 하지 않는다.

핵심 질문:

```text
현재 numeric gap/overlap/height proxy를 넘어서,
standing on / lying on / supported by를 설명할 수 있는
predicate-independent geometry evidence를 만들 수 있는가?
```

## Source Basis

```text
support_rows = 161498
distinct_scans = 1157
distinct_directed_pairs = 75763
scan_asset_complete_rate = 1.0
semseg_both_objects_present_rate = 1.0
mesh_contact_surface_possible_rate = 1.0
sequence_multiview_possible_rate = 1.0
```

This allows a feature probe, not a learned model.

## Probe Tiers

Tier A: full-row cheap geometry evidence

- source: `semseg.v2.json`;
- scope: all `161,498` support/contact rows;
- features:
  - subject/object OBB center, extents, axis length ratios;
  - signed vertical gap and OBB contact proxy;
  - subject uprightness / horizontalness;
  - object support flatness;
  - dominant-normal upness and normal alignment.

Tier B: stratified sample point/mesh evidence

- source: `labels.instances.align.annotated.v2.ply`, `mesh.refined.v2.obj`, mesh segment json;
- scope: `1,200` row stratified probe sample;
- features:
  - object point count;
  - percentile bbox and PCA axis features;
  - bottom contact band density;
  - near-surface point ratio;
  - contact patch / support area proxy;
  - point-to-surface gap histogram.

Tier C: optional multi-view / `Q_e`

- source: `sequence.zip`;
- scope: small audit-only sample;
- role: co-visible frame count, color/depth/pose availability, crop quality proxy;
- status: `Q_e` / audit-first only, not immediate `C_e` model input.

## Sampling Policy

```text
Tier A = all support/contact rows
Tier B = 1200 stratified rows
Tier B non-hard-surface priority = at least 360 rows if available
Tier C multi-view sample = 120 rows
```

Tier B should be balanced by:

- predicate: `standing on`, `lying on`, `supported by`;
- hard-surface vs non-hard-surface pair;
- geometry status where possible;
- scan and visible-pair caps.

`queue_kind`, `geometry_status`, and source rank are audit strata only. They must not become
model features.

## Required Probe Metrics

The next runner must report:

- feature non-missing rate;
- finite numeric rate;
- predicate-wise feature distribution;
- hard-surface sensitivity;
- HL/LH queue sensitivity;
- blocked-field absence;
- correlation or redundancy against old numeric gap/overlap/height proxy.

Promotion to any materialization plan requires:

```text
Tier A feature derivability >= 0.95
retained feature finite numeric rate >= 0.99
new mesh/pose/contact features are not identical to old numeric proxy
hard-surface and queue risks are explicitly quantified
model-safe feature table contains no source/label/construction fields
```

## Leakage Controls

Blocked model inputs:

```text
source_score
semantic_rank
rank_band
queue_kind
geometry_status
h001_verification_status
label_match_status
machine_hint
counterfactual_type
row_role
human_label
```

Allowed feature inputs:

```text
scan_id for asset join
subject_id
object_id
semseg OBB
dominantNormal
aligned PLY objectId vertices
mesh segment files
```

Allowed audit strata:

```text
predicate_label
hard_surface_pair
queue_kind
geometry_status
visible_pair
scan_id
```

## Decision

```text
feature_probe_allowed = true
tier_a_full_semseg_probe = true
tier_b_ply_mesh_sample_probe = true
multiview_qe_audit_first = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
paper_evidence_allowed = false
```

## Next Runner Contract

```text
next = compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner
```

The next runner should produce:

- `feature_schema.json`;
- `tier_a_semseg_feature_summary.csv`;
- `tier_b_ply_mesh_probe_summary.csv`;
- `feature_derivability.csv`;
- `feature_distribution_diagnostics.csv`;
- `old_numeric_dominance_diagnostics.csv`;
- `shortcut_risk_diagnostics.csv`;
- `model_safe_feature_preview.jsonl`;
- `audit_feature_preview.jsonl`;
- `path_decision.json`;
- `summary.json`;
- `report.md`;
- `validation_errors.jsonl`.

## Boundary

- Train-only feature-probe plan.
- No candidate materialization.
- No learned smoke.
- No validation/test usage.
- No paper-level evidence promotion.
- No H001 artifact modification.
