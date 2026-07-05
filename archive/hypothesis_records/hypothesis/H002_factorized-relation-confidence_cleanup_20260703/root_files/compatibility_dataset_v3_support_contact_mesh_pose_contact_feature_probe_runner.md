# Compatibility Dataset V3 Support/Contact Mesh-Pose-Contact Feature Probe Runner

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner/
status = h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_ready_for_result_review
selected_path = review_mesh_pose_contact_features_before_materialization
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_feature_probe_result_review
```

## Purpose

This runner executes the train-only feature probe selected by the previous
mesh/pose/contact feature-probe plan. It checks whether support/contact relation
candidates can expose usable predicate-independent geometry evidence `G_e`
beyond the older gap/overlap/distance proxies.

It does not create a compatibility target, train a model, or authorize
support/contact learned smoke.

## Inputs

```text
plan = artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan/
source_inventory = artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory/
rga_queues = artifacts/train_rga_full/open3dsg_train_full/rga/
scan_assets = local_dataset/3RScan/scans/
```

The runner scans only the train-side support/contact queue rows:

```text
standing on
lying on
supported by
```

## Output Artifacts

```text
feature_schema.json
tier_a_semseg_feature_summary.csv
tier_b_ply_mesh_probe_summary.csv
feature_derivability.csv
feature_distribution_diagnostics.csv
old_numeric_dominance_diagnostics.csv
shortcut_risk_diagnostics.csv
model_safe_feature_preview.jsonl
audit_feature_preview.jsonl
path_decision.json
summary.json
report.md
validation_errors.jsonl
```

## Counts

```text
support_rows = 161498
tier_a_records = 161498
tier_b_records = 1200
tier_b_distinct_scans = 654
tier_b_hard_surface_rows = 408
tier_b_non_hard_surface_rows = 792
```

## Tier A: Full Semseg OBB / Normal Probe

Tier A derives semseg-level OBB and dominant-normal features for all support/contact
rows. The main feature families are:

- vertical center and surface-gap cues;
- XY overlap and support-area proxies;
- normalized center distance;
- subject/object pose and flatness proxies;
- dominant-normal upness and normal alignment;
- OBB-level contact likelihood proxy.

All Tier A features passed derivability and finite-value gates:

```text
tier_a_derivability_pass = true
tier_a_finite_pass = true
```

## Tier B: Stratified PLY Contact Proxy Probe

Tier B derives point-level contact proxies from aligned instance PLY files on a
stratified 1,200-row sample. The sample intentionally oversamples non-hard-surface
rows and caps scans / visible pairs so the probe is not only a floor-wall artifact.

The main feature families are:

- subject/object point counts;
- point-level signed and absolute surface gap;
- point-level XY overlap ratios;
- subject/object vertical extent;
- bottom/top band density;
- local contact-candidate point ratio.

Tier B passed the sample-size gate:

```text
tier_b_sample_pass = true
```

## Leakage And Proxy Checks

The model-safe preview excludes blocked source/construction/label fields:

```text
model_safe_blocked_fields_absent = true
```

The new features are not rejected as direct copies of old numeric proxy fields:

```text
new_features_not_old_proxy_pass = true
high_old_numeric_correlations_excluding_contact_proxy = []
```

This means the feature probe is worth reviewing. It does not yet mean the features
are sufficient for a learned support/contact compatibility benchmark.

## Remaining Risks

```text
hard_surface_dominance = 0.7023059109091134
queue_imbalance = {"HL": 1069, "LH": 160429}
```

Several features also show high HL/LH queue shifts. This is expected because the
queue split is not an independent label. Queue kind, geometry status, source score,
rank, and construction fields remain audit-only.

## Path Decision

```text
feature_probe_result_review_allowed = true
candidate_materialization_allowed = false
learned_smoke_allowed = false
paper_evidence_allowed = false
```

Interpretation:

The source-availability and feature-derivability blockers are cleared. The target
construction blocker is not cleared. The next step should review feature
distributions, proxy independence, and hard-surface/queue sensitivity before deciding
whether any support/contact materialization is justified.

## Boundary

- train-only feature probe;
- no validation/test usage;
- no H001 artifact modification;
- no candidate materialization;
- no learned smoke;
- no paper evidence.

## Next

```text
compatibility_dataset_v3_support_contact_feature_probe_result_review
```
