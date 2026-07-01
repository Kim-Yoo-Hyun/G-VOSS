# H002 Compatibility Routing Commands

This file records the future command contract for H002 Docker promotion.

No command in this file has produced paper-level H002 metrics.

## Planned Commands

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-protocol-check
```

Expected outputs:

```text
mount_check.json
validation_errors.jsonl
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/preflight/latest/
```

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialize-routes
```

Expected outputs:

```text
route_rows.jsonl
model_safe_view.jsonl
hidden_manifest.jsonl
row_manifest.json
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/materialization/latest/
```

Observed row counts:

```text
route_rows = 6952
model_safe_view = 6952
hidden_manifest = 6952
validation_errors = 0
```

```bash
docker compose -f configs/h002/compose.yaml run --rm h002-shortcut-audit
```

Expected outputs:

```text
shortcut_audit.csv
control_metrics.csv
validation_errors.jsonl
```

Current implemented audit command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-materialization-schema-audit
```

Expected outputs:

```text
audit_manifest.json
schema_violations.jsonl
blocked_field_hits.jsonl
high_shortcut_warnings.jsonl
shortcut_risk_table.csv
split_readiness_table.csv
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/schema_audit/latest/
```

Observed audit counts:

```text
schema_error_count = 0
blocked_C_e_field_hit_count = 0
high_C_e_allowed_shortcut_warning_count = 0
split_readiness_family_count = 4
```

Current implemented split command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-split
```

Expected outputs:

```text
model_safe_split_view.jsonl
split_assignments.jsonl
group_manifest.jsonl
split_manifest.json
route_split_counts.csv
predicate_split_counts.csv
leakage_audit.csv
validation_errors.jsonl
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/splits/latest/
```

Observed split counts:

```text
model_safe_split_view = 6952
split_assignments = 3684
group_manifest = 3684
validation_errors = 0
cv_group_single_split_violations = 0
official_validation_test_usage = 0
```

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-grouped-eval
```

Expected outputs:

```text
eval_manifest.json
model_view_manifest.json
route_metrics.csv
predicate_metrics.csv
control_metrics.csv
prediction_scores.jsonl
leakage_audit.csv
validation_errors.jsonl
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/evaluation/latest/
```

Observed internal heldout summary:

```text
M1_T_semantic_only AUROC = 0.454321
M2_G_geometry_only AUROC = 0.487690
M3_T_plus_G_concat AUROC = 0.465868
M4_TxG_compatibility AUROC = 0.984976
C1_wrong_T_control AUROC = 0.014425
C2_shuffled_G_control AUROC = 0.493975
validation_errors = 0
```

Boundary: this is an internal H002 candidate-pool grouped holdout run. It is not an official validation/test metric and is not a paper-level result. The result-review and claim-boundary stages have passed only for hypothesis-stage `C_e` claims.

Optional calibration command, only if calibrated `p_rel` / `p_obs` claims remain active:

```bash
docker compose -f configs/h002/compose.yaml run --rm h002-calibration
```

Expected outputs:

```text
calibration_metrics.csv
selective_risk.csv
reliability_diagram_data.csv
```

## Current Next Command

Grouped-eval feature extractor repair has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis/
```

Repaired grouped-eval claim-boundary review has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/
```

Official validation/test protocol planning has completed under:

```text
compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review
```

Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/
```

Official source inventory stage:

```text
compatibility_dataset_v3_official_source_inventory_after_protocol_plan
```

Official source inventory has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
```

Observed inventory:

```text
relative_horizontal GT = 5474, OBB pair coverage = 1.0
relative_vertical GT = 390, OBB pair coverage = 1.0
size_relative GT = 170, OBB pair coverage = 1.0
support_contact GT = 1589, OBB pair coverage = 1.0
validation_errors = 0
official_validation_metric = false
paper_metric = false
```

Official candidate materialization protocol stage:

```text
compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory
```

The protocol must define model-safe views, hidden manifests, GT/counterfactual
construction, source-candidate bridge handling, family-specific `G_e`, and
leakage/shortcut audits before any paper-level H002 metric is generated. `Z_e`
and `Q_e` still must not be folded into the main `C_e` claim without a separate
`p_rel` / `p_obs` protocol.

Official candidate materialization protocol has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
```

The next command to implement is:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-materialize-candidates
```

Expected outputs:

```text
experiments/H002_compatibility_routing/official_materialization/latest/candidate_rows.jsonl
experiments/H002_compatibility_routing/official_materialization/latest/model_safe_view.jsonl
experiments/H002_compatibility_routing/official_materialization/latest/hidden_manifest.jsonl
experiments/H002_compatibility_routing/official_materialization/latest/row_manifest.json
experiments/H002_compatibility_routing/official_materialization/latest/validation_errors.jsonl
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/official_materialization/latest/
```

Observed counts:

```text
candidate_rows = 23062
model_safe_view = 23062
hidden_manifest = 23062
validation_errors = 0
official_validation_metric = false
paper_metric = false
```

This command did not compute official validation metrics and did not use
official test.

Official materialization schema/shortcut audit command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-materialization-schema-audit
```

Expected outputs:

```text
experiments/H002_compatibility_routing/official_schema_audit/latest/audit_manifest.json
experiments/H002_compatibility_routing/official_schema_audit/latest/schema_violations.jsonl
experiments/H002_compatibility_routing/official_schema_audit/latest/blocked_field_hits.jsonl
experiments/H002_compatibility_routing/official_schema_audit/latest/separation_audit.csv
experiments/H002_compatibility_routing/official_schema_audit/latest/label_balance.csv
experiments/H002_compatibility_routing/official_schema_audit/latest/shortcut_risk_table.csv
experiments/H002_compatibility_routing/official_schema_audit/latest/high_shortcut_warnings.csv
experiments/H002_compatibility_routing/official_schema_audit/latest/control_readiness.csv
experiments/H002_compatibility_routing/official_schema_audit/latest/report.md
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/official_schema_audit/latest/
```

Observed audit summary:

```text
schema_violations = 0
blocked_field_hits = 0
runtime_validation_errors = 0
model_safe_rows = 23062
hidden_rows = 23062
model_safe_hidden_mismatch = 0
control_readiness_blockers = 0
shortcut_warnings = 1
support_contact_predicate_x_class_pair_majority_accuracy = 0.993707
official_validation_metric = false
paper_metric = false
```

Boundary: this command did not compute official metrics and did not use official
test. The `support_contact` shortcut warning blocks solved/main
`support_contact` claims, but does not block protocol freeze for official
validation metrics.

The next command/stage is metric protocol freeze:

```text
compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit
```

The freeze must lock family-wise, macro-family, weighted-family, and secondary
overall metrics; wrong-`T`, shuffled-`G`, and route-specific controls; `Z_e`
exclusion from main `C_e`; and `support_contact` challenging-route wording
before running any official metric.

Metric protocol freeze command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
```

Observed protocol summary:

```text
status = h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready
validation_errors = 0
official_validation_eval_only = true
primary_metric = macro_family_AUROC
main_C_e_allowed_blocks = T_e,G_e
z_e_excluded_from_main_C_e = true
q_e_excluded_from_main_C_e = true
support_contact_claim = challenging_not_solved
official_validation_metric = false
paper_metric = false
```

The next Docker command to implement is:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-metric-runner
```

Expected output root:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

The runner must write `family_metrics.csv`, `predicate_metrics.csv`,
`aggregate_metrics.csv`, `control_metrics.csv`, `prediction_scores.jsonl`,
`leakage_audit.csv`, `eval_manifest.json`, and `validation_errors.jsonl`.
It must not fit or tune on official validation and must not use official test.

Status: completed, exit 0. Runtime output root:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

Observed official validation metric snapshot:

```text
M1_T_semantic_only macro_family_AUROC = 0.41763347769299586
M2_G_geometry_only macro_family_AUROC = 0.5
M3_T_plus_G_concat macro_family_AUROC = 0.4169228221289655
M4_TxG_compatibility macro_family_AUROC = 0.8355465299908279
M4_TxG_compatibility weighted_family_AUROC = 0.7207808044279794
M4_TxG_compatibility overall_AUROC = 0.724835499373417
validation_errors = 0
official_test_usage = false
paper_metric = false
```

Observed caveats:

```text
support_contact M4 AUROC = 0.6317116456316851
horizontal_frame_swap macro delta AUROC = 0.03814880004643195
```

Stage artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
```

Next stage:

```text
compatibility_dataset_v3_official_metric_result_review_after_runner
```

Official metric result review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_official_metric_result_review_after_runner.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
```

Observed review decision:

```text
paper_level_experiment_execution_gate = passed_with_caveats
paper_result_promotion = not_yet
main_candidate_families = relative_vertical,size_relative
conditional_candidate_families = relative_horizontal
diagnostic_families = support_contact
validation_errors = 0
```

Korean report:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0702.md
```

Next stage:

```text
compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```
