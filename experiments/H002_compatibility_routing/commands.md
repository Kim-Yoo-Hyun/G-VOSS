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

Source-reranking materialization command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-materialize
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/source_reranking_materialization/latest/
```

Observed output counts:

```text
source_candidates = 762888
model_safe_ce_view = 762888
model_safe_geometry_only_view = 762888
source_rank_view = 762888
hidden_metric_manifest = 762888
validation_errors = 0
```

Boundary: no source reranking metric, official test, or paper result was
produced. The next command should be a source-reranking materialization schema
audit, not metric freeze.

Source-reranking materialization schema audit command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-schema-audit
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
```

Observed audit result:

```text
validation_errors = 0
blocked_field_hits = 0
candidate_id_alignment = pass
C_e view blocks = T_e + G_e only
primary_success_families = relative_vertical,size_relative balanced
support_contact = diagnostic excluded
```

Boundary: no source reranking metric, official test, or paper result was
produced. The next command should freeze the source-reranking metric protocol.

Source-reranking metric protocol freeze command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit/
```

Observed protocol summary:

```text
status = h002_source_reranking_metric_protocol_freeze_after_schema_audit_ready
primary_score = S2_source_x_Ce
K_grid = 5,10,20,50,100
primary_success_families = relative_vertical,size_relative
support_contact = diagnostic excluded
validation_errors = 0
official_test_usage = false
metric_runner_executed = false
```

The next command to implement/run is:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-metric-runner
```

Expected output root:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

The runner must compute `Recall@K`, `Violation@K`, and `Selected@K` for `S0`,
`S1`, `S2`, and frozen controls. It must not fit/tune on official validation and
must not use official test.

Status: completed, exit 0. Runtime output root:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

Observed output:

```text
metric_manifest.json
score_manifest.json
source_family_metrics.csv
score_condition_metrics.csv
control_metrics.csv
selected_predictions.jsonl
validation_errors.jsonl
```

Observed runtime summary:

```text
source_rows_scored = 762888
internal_train_rows_for_C_e = 4868
selected_prediction_rows = 932732
validation_errors = 0
official_test_usage = false
```

Primary weighted `S2_source_x_Ce` versus `S0_source_score`:

```text
K=5   delta_Recall@K=+0.007937  delta_Violation@K=-0.240690
K=10  delta_Recall@K=+0.041950  delta_Violation@K=-0.229859
K=20  delta_Recall@K=+0.081633  delta_Violation@K=-0.243091
K=50  delta_Recall@K=+0.103175  delta_Violation@K=-0.259199
K=100 delta_Recall@K=+0.004535  delta_Violation@K=-0.142873
```

The next stage is source-reranking metric result review, not final paper
promotion.

Source-reranking metric result review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner/
```

Review summary:

```text
source_reranking_validation_evidence = positive
negative_recall_cells = 3 / 20
violation_nonimprove_cells = 0 / 20
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review
```

The next stage is claim-boundary lock.

Source-reranking claim-boundary lock command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review/
```

Locked summary:

```text
status = h002_source_reranking_claim_boundary_lock_after_result_review_locked
validation_errors = 0
table_role = secondary_validation_table_candidate_or_appendix
official_test_usage = false
final_paper_result_promotion = not_yet
next_todo = compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock
```

The next stage is a validation table skeleton that preserves the validation-only
boundary and the 3/20 source-family-K recall-regression caveat.

Source-reranking validation table skeleton command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock/
```

Observed output:

```text
status = h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_ready
validation_errors = 0
primary_tradeoff_rows = 5
control_rows = 15
required_caveat_rows = 3
next_todo = compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton
```

Source-reranking validation table review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton/
```

Observed output:

```text
status = h002_source_reranking_validation_table_review_after_skeleton_ready
validation_errors = 0
validation_table_position = appendix_or_secondary_analysis_only
test_benchmark_ready_now = false
next_todo = compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade
```

Test benchmark preflight command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade/
```

Observed output:

```text
status = h002_test_benchmark_preflight_after_validation_downgrade_ready_blocked
validation_errors = 0
canonical_test_file_exists = false
validation_alias_test_candidates = 2
official_test_source_rows = 0
experiments_test_run_allowed = false
next_todo = compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight
```

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

Official metric claim-boundary lock command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review/
```

Observed lock decision:

```text
claim_boundary_locked = true
paper_table_draft_allowed = true
final_paper_result_promotion = not_yet
primary_mechanism_families = relative_vertical,size_relative
caveated_mechanism_families = relative_horizontal
diagnostic_families = support_contact
validation_errors = 0
```

Next stage:

```text
compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock
```

Paper table skeleton command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock/
```

Observed skeleton decision:

```text
paper_table_skeleton_ready = true
final_paper_result_promotion = not_yet
primary_table_scope = relative_vertical + size_relative
caveated_rows = relative_horizontal
diagnostic_rows = support_contact
validation_errors = 0
```

Primary skeleton metric:

```text
C_e compatibility AUROC = 0.995453
T_e only AUROC = 0.500000
G_e only AUROC = 0.500000
T_e + G_e concat AUROC = 0.498994
```

Next stage:

```text
compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock
```

Paper table skeleton review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock/
```

Observed review decision:

```text
principled_structure = true
natural_design_flow = true
keep_as_bounded_mechanism_evidence = true
table_is_standalone_paper_result = false
final_paper_result_promotion = not_yet
main_reason_not_promoted = primary evidence is strong but too clean/signed-comparison-heavy
validation_errors = 0
```

Next stage:

```text
compatibility_dataset_v3_principled_design_gap_plan_after_table_review
```

Principled design gap plan command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_principled_design_gap_plan_after_table_review.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review/
```

Observed gap decision:

```text
principled_structure_kept = true
current_table_role = bounded_mechanism_evidence
final_paper_result_promotion = not_yet
selected_gap = harder_support_contact_route
source_deployable_experiment = defer_until_harder_route_stable
p_obs_p_rel_branch = defer_until_independent_observability_labels
validation_errors = 0
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan
```

## Support/Contact Harder Route Protocol After Gap Plan

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan/
```

Observed protocol decision:

```text
selected_route = support_contact_harder_route
main_predicates = standing on; lying on
diagnostic_predicates = supported by
main_c_e_inputs = T_e; G_e
z_e_excluded_from_main_c_e = true
q_e_excluded_from_main_c_e = true
official_test_usage = false
paper_metric_promoted = false
validation_errors = 0
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol
```

## Support/Contact Harder Route Source Inventory After Protocol

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol/
```

Observed inventory:

```text
official_validation_support_contact_rows = 3178
official_validation_support_contact_scans = 156
train_point_multiview_rows = 800
train_point_multiview_main_rows = 640
validation_errors = 0
current_official_G_e = OBB_proxy_only
official_test_usage = false
paper_metric_promoted = false
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory
```

## Support/Contact Harder Route Materialization Plan After Source Inventory

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory/
```

Observed plan:

```text
official_validation_support_contact_rows = 3178
same_pair_predicate_flip_groups = 1589
paired_groups_ok = 1589
mixed_predicate_class_cells = 8
mixed_predicate_class_balanced_rows = 40
primary_view = model_safe_main_no_class
official_test_usage = false
paper_metric_promoted = false
validation_errors = 0
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan
```

Planned Docker implementation boundary:

```text
script = experiments/H002_compatibility_routing/scripts/materialize_support_contact_harder_route.py
service = h002-support-contact-hard-materialize
output_root = experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```

The planned materializer must not run metrics. It should only write row-level
materialization outputs and validation/schema precheck artifacts.

## Support/Contact Harder Route Docker Materialization After Plan

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-materialize
```

Status: completed, exit 0. Runtime output root:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```

Observed output:

```text
candidate_rows = 3178
model_safe_main_no_class = 3178
model_safe_main_with_class_ablation = 3178
model_safe_geometry_only = 3178
model_safe_qe_diagnostic = 3178
hidden_manifest = 3178
group_manifest = 1589
richer_G_e_feature_count = 43
validation_errors = 0
official_test_usage = false
metrics_run = false
```

Stage review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan/
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization
```

## Support/Contact Harder Route Schema Shortcut Audit After Docker Materialization

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-schema-audit
```

Status: completed, exit 0. Runtime output root:

```text
experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest/
```

Observed output:

```text
rows = 3178
groups = 1589
richer_G_e_feature_count = 43
validation_errors = 0
blocked_field_hits = 0
control_readiness = 7/7
shortcut_warnings = 3
high_shortcut_warnings = 2
```

Main shortcut warnings:

```text
primary_predicate_only_majority = 0.853996
hidden_predicate_x_class_pair_majority = 0.993707
class_ablation_predicate_x_class_pair_majority = 0.993707
```

Stage review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization/
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit
```

## Support/Contact Harder Route Metric Protocol Freeze After Schema Shortcut Audit

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit/
```

Observed output:

```text
status = h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready
validation_errors = 0
primary_metric = support_contact_AUROC
primary_model = M4_TxG_compatibility
baseline_models = M1_predicate_only, M2_geometry_only, M3_T_plus_G_concat
controls = wrong_T_same_route, shuffled_G_global, shuffled_G_within_class_pair
diagnostics = class_ablation, Q_e, predicate_x_class_pair
official_validation_policy = eval_only
official_test_usage = false
metric_runner_next = false
train_eval_feature_parity = needs_alignment_audit
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze
```

Do not run the metric runner before train/eval feature alignment passes. The
official validation hard-route view has `43` canonical `G_e` features, while the
available train reference has a different prefixed `63`-feature schema.

## Support/Contact Harder Route Train/Eval Alignment After Metric Protocol Freeze

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze/
```

Observed output:

```text
status = h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_ready
validation_errors = 0
official_features = 43
mapped_train_features = 43
direct_or_transform = 31
derived_or_proxy = 12
aligned_rows = 640
internal_train_rows = 531
internal_dev_rows = 109
scan_overlap_with_official_validation = 0
endpoint_overlap_with_official_validation = 0
```

Runner-ready inputs:

```text
model_safe_no_class_train_dev.jsonl
class_ablation_train_dev.jsonl
hidden_train_dev_manifest.jsonl
runner_input_contract.json
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment
```

## Support/Contact Harder Route Metric Runner After Train/Eval Alignment

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-metric-runner
```

Status: completed, exit 0. Runtime output root:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
```

Observed output:

```text
status = h002_support_contact_harder_metric_runner_ready
validation_errors = 0
internal_train_rows = 531
internal_dev_rows = 109
official_validation_rows = 3178
internal_dev_M4_AUROC = 0.721356
official_validation_M4_AUROC = 0.077539
official_validation_M2_geometry_AUROC = 0.500000
official_validation_M3_concat_AUROC = 0.454660
official_validation_wrong_T_AUROC = 0.922461
official_test_usage = false
paper_metric_promoted = false
```

Stage review command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment/
```

Next stage:

```text
compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner
```

## Test Benchmark Source Resolution After Preflight

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight/
```

Observed output:

```text
status = h002_test_benchmark_source_resolution_after_preflight_ready_blocked
validation_errors = 0
selected_path = official_eval_server_not_confirmed_keep_validation_appendix_request_external_provenance
accepted_official_eval_server_confirmed = false
independent_relation_test_label_confirmed = false
scan_level_3rscan_test_split_exists = true
scan_level_split_is_sufficient_for_h002 = false
relation_test_source_predictions_available = false
experiments_test_run_allowed = false
```

Next stage:

```text
compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution
```

Do not run a test benchmark metric runner yet. The next command should prepare
or verify external provenance for an official evaluation server or independent
3DSSG relation-test label/source-prediction pool.

## External Provenance Request After Source Resolution

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution/
```

Observed output:

```text
status = h002_test_benchmark_external_provenance_request_after_source_resolution_ready
validation_errors = 0
selected_path = external_request_packet_ready_keep_test_benchmark_blocked
request_packet_ready = true
test_benchmark_execution_allowed = false
checkpoint_reproduction_is_sufficient = false
prediction_only_test_scan_export_is_sufficient = false
```

Next stage:

```text
compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request
```

Do not run a test benchmark metric runner before official response or
documentation ingestion.

## External Response Ingestion After Request

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request/
```

Observed output:

```text
status = h002_test_benchmark_external_response_ingestion_after_request_ready_blocked_no_external_response
validation_errors = 0
selected_path = no_external_response_keep_test_benchmark_blocked_select_validation_position_lock
external_response_found = false
candidate_response_files = 0
test_benchmark_execution_allowed = false
validation_table_position = appendix_or_secondary_analysis_only
```

Next stage:

```text
compatibility_dataset_v3_validation_only_position_lock_after_no_external_response
```

Do not run a test benchmark metric runner. A later official response should be
placed in the response inbox and this ingestion command should be rerun before
changing benchmark status.

## Validation-Only Position Lock After No External Response

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response/
```

Observed output:

```text
status = h002_validation_only_position_lock_after_no_external_response_ready
validation_errors = 0
selected_path = validation_only_appendix_secondary_lock_keep_test_benchmark_blocked
paper_position = appendix_or_secondary_analysis
official_test_benchmark = false
open3dsg_source_boundary = open_vocabulary_source_closed_vocabulary_3dssg_mapping
```

Next stage:

```text
compatibility_dataset_v3_h002_post_validation_position_path_decision
```

Do not run a test benchmark metric runner from this state. Current H002
source-reranking metrics are validation-level custom-protocol evidence.

## H002 Post-Validation Position Path Decision

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_h002_post_validation_position_path_decision.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision/
```

Observed output:

```text
status = h002_post_validation_position_path_decision_ready
validation_errors = 0
selected_path = promote_official_validation_as_main_comparative_claim_keep_test_blocked
main_claim_split = official_3DSSG_validation_split
main_table_allowed = true_validation_benchmark
official_test_benchmark = false
open3dsg_source_boundary = open_vocabulary_source_closed_vocabulary_3dssg_mapping
```

Next stage:

```text
compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision
```

Do not run a new metric runner from this state. The next step is to lock table
caption, allowed baseline wording, and blocked official-test/SOTA wording.

## Main Validation Claim Table Lock After Path Decision

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision/
```

Observed output:

```text
status = h002_main_validation_claim_table_lock_after_path_decision_ready
validation_errors = 0
selected_path = main_validation_table_claim_locked_keep_official_test_blocked
main_table = official_3DSSG_validation_split
official_test_benchmark = false
h003_embedding_extension_in_main_claim_now = false
```

Next stage:

```text
compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock
```

Do not run new metrics from this state. Materialize compact caption-ready table
rows from the existing validation source-reranking artifacts.
