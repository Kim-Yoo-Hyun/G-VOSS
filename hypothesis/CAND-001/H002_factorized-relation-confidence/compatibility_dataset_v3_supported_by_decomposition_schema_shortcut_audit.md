# H002 R6 Supported-By Decomposition Schema Shortcut Audit

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit/
status = h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_ready_for_smoke_plan
selected_path = schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_smoke_plan
```

## Result

R6 `supported by` decomposition target passed schema and shortcut audit.

```text
rows = 320
accept_broad_support = 80
relabel_to_subtype = 80
reject_no_support = 80
abstain = 80
observable_rows = 240
schema_leakage_hits = 0
allowed_high_risk_probes = 0
allowed_medium_risk_probes = 10
hidden_high_risk_probes = 8
```

## Interpretation

- `model_safe_rows` contain only `T_e`, `G_e_mesh_pose_contact`, `Q_e`, and target labels.
- No hidden/source/GT/construction field appears inside model-safe feature blocks.
- No allowed model-safe probe reaches high-risk shortcut level.
- Medium-risk allowed probes are mostly single `G_e` features such as `obb_contact_likelihood_proxy`, `center_delta_z`, `support_area_proxy`, and `xy_overlap_min_ratio`.
- Hidden `evidence_reason`, `label_match_status`, `candidate_role`, `machine_hint`, and `matched_predicates` can nearly copy the target if leaked, so they must remain hidden/control-only.
- `no_gt_for_pair` appears only in `abstain`, not in `reject_no_support`; this preserves the no-GT-not-negative policy.

## Claim Boundary

This audit does not prove learned reliability or paper-level performance. It only
shows that the R6 decomposition rows are schema-clean enough to plan a train-only
smoke test.

Next step:

```text
compatibility_dataset_v3_supported_by_decomposition_smoke_plan
```
