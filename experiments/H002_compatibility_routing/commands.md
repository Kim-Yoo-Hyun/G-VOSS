# H002 Compatibility Routing Commands

This file records H002 Docker/runtime commands and the current command boundary.

The current paper-facing result is a validation-level table candidate, not an
official-test or SOTA benchmark. The latest completed H002 Docker step is the
repaired-Q_e p_obs metric review. The review demotes `p_obs` from the core
paper claim to optional diagnostic/future evidence.

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

Source-reranking sensitivity command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-sensitivity
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/
```

Observed result:

```text
source_rows_scored = 762888
validation_errors = 0
no_route_g_only_sensitivity = passed
raw_source_x_Ce_direction = preserved_vs_S0_at_K_10_20_50
rankpct_normalization = violation_reduction_but_low_K_recall_loss
sensitivity_pass = false
```

Boundary: this sensitivity does not replace the frozen main validation table. It
supports the scoped claim that S2 is not explained by a no-route G-only
baseline, while blocking normalization-invariant wording.

Historical placeholder calibration command, superseded by
`h002-pobs-prel-calibration-upgrade`:

```bash
# no longer used
```

Expected outputs:

```text
calibration_metrics.csv
selective_risk.csv
reliability_diagram_data.csv
```

## Completed Source-Reranking Chain

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

Boundary: this materialization produced source-wide views only. Later stages
completed schema audit, metric freeze, metric run, result review, claim lock,
table materialization, and table review.

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
absolute_primary_metrics.csv
control_metrics.csv
selected_predictions.jsonl
validation_errors.jsonl
```

Observed runtime summary:

```text
source_rows_scored = 762888
internal_train_rows_for_C_e = 4868
selected_prediction_rows = 3264562
A1_source_x_G_only = implemented
A2_source_x_TG_concat = implemented
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

After the H002 ablation-expansion run, the implementation artifact is:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
```

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

Next stage at that time:

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

Next stage at that time:

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

## Main Validation Table Materialization After Claim Lock

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
```

Observed output:

```text
status = h002_main_validation_table_materialization_after_claim_lock_ready
validation_errors = 0
selected_path = main_validation_table_materialized_select_review
main_table_rows = 5
source_family_caveat_rows = 3
control_rows = 15
official_test_usage = false
h003_embedding_extension_in_main_claim_now = false
```

Next stage:

```text
compatibility_dataset_v3_main_validation_table_review_after_materialization
```

This command does not run new metrics. It reads the frozen validation
source-reranking outputs and materializes caption-ready table rows plus caveats.

## Main Validation Table Review After Materialization

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_main_validation_table_review_after_materialization.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization/
```

Observed output:

```text
status = h002_main_validation_table_review_after_materialization_ready
validation_errors = 0
selected_path = main_validation_table_reviewed_select_paper_insertion_plan
next_todo = compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review
```

Boundary: do not run a new H002 Docker metric from this state. The next task is
to decide paper insertion location, caption, footnote, and caveat wording for
the reviewed validation table.

## Paper Draft Insertion Plan After Review

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review/
```

Observed output:

```text
status = h002_paper_draft_insertion_plan_after_main_validation_table_review_ready
validation_errors = 0
selected_path = paper_draft_insertion_plan_locked_no_manuscript_edit
next_todo = compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan
```

Boundary: this step edits no manuscript files. It freezes the H002 validation
table insertion plan, caption, footnote, draft snippets, and blocked wording.

## p_obs / p_rel Selective-Decision Chain

This chain evaluates the H002 selective-decision extension after the p_obs /
p_rel protocol freeze. It is a validation-level stress test with synthetic
missing-evidence controls, not an official-test benchmark.

Materialization:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-materialize
```

Expected outputs:

```text
experiments/H002_compatibility_routing/pobs_prel_materialization/latest/
  model_safe_qe_view.jsonl
  model_safe_prel_view.jsonl
  hidden_selective_labels.jsonl
  materialization_manifest.json
  validation_errors.jsonl
```

Status: completed, exit 0. Observed output:

```text
input_observed_rows = 30014
output_rows_per_view = 150070
synthetic_unobservable_control = 120056
official_validation = 115310
validation_errors = 0
```

Schema audit:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-schema-audit
```

Expected outputs:

```text
experiments/H002_compatibility_routing/pobs_prel_schema_audit/latest/
  summary.json
  schema_separation_audit.csv
  label_balance.csv
  blocked_field_hits.jsonl
  validation_errors.jsonl
```

Status: completed, exit 0. Observed audit:

```text
blocked_field_hits = 0
validation_errors = 0
qe_rows = 150070
prel_rows = 150070
hidden_rows = 150070
```

Selective metric:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-metric-runner
```

Expected outputs:

```text
experiments/H002_compatibility_routing/pobs_prel_evaluation/latest/
  gate_decision.json
  eval_manifest.json
  pobs_metrics.csv
  prel_metrics.csv
  decision_metrics.csv
  missing_evidence_control_metrics.csv
  risk_coverage_curve.csv
  prediction_scores.jsonl
  validation_errors.jsonl
```

Status: completed, exit 0. Gate result:

```text
selective_metric_pass = true
paper_promotion_pass = false
p_obs AUROC = 1.000000
p_rel AUROC = 0.724615
decision macro-F1 = 0.778449
missing-control abstain rate = 1.000000
p_rel ECE@10 = 0.171030
validation_errors = 0
```

Boundary: this is a selective stress-test with synthetic missing-evidence
controls. It does not yet promote a calibrated p_obs/p_rel quantitative paper
claim.

Calibration-upgrade command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-calibration-upgrade
```

Expected outputs:

```text
experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/
  summary.json
  calibration_metrics.csv
  calibrator_selection.csv
  reliability_diagram.csv
  risk_coverage_curve.csv
  selective_metrics.csv
  missing_evidence_control_metrics.csv
  failure_route_connection.csv
  bootstrap_ci.csv
  observability_asset_audit_labels.csv
  prediction_scores.jsonl
  validation_errors.jsonl
```

Status: completed, exit 0. Gate result:

```text
calibrated_quantitative_claim_pass = false
pobs_prel_framework_component_allowed = true
asset_audit_rows = 23062
asset_observability_label_counts = observable:23062
p_obs calibrated ECE@10 = 0.000001
p_rel calibrated AUROC = 0.723800
p_rel raw ECE@10 = 0.171030
p_rel calibrated ECE@10 = 0.223458
decision macro-F1 calibrated = 0.778072
AURC = 0.147590
missing-control abstain rate = 1.000000
attachment_containment_rows_present = false
validation_errors = 0
```

Boundary: the six requested p_obs / p_rel checks have been run, but the result
does not allow wording that calibrated p_obs / p_rel reliability is solved.
Use it as a framework component and stress-test result only.

## H002 Paper Outline / Integration Decision

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan/
```

Observed output:

```text
status = h002_paper_outline_or_integration_decision_after_insertion_plan_ready
selected_path = open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root
validation_errors = 0
h001_manuscript_edit_now = false
new_top_level_paper_folder_now = false
next_todo = compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision
```

## H002 Standalone Outline Gap Review

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision/
```

Observed output:

```text
status = h002_standalone_outline_gap_review_after_decision_ready
selected_path = keep_outline_candidate_do_not_promote_paper_workspace_yet_resolve_gap_pack
validation_errors = 0
blocking_gates = G1_claim_thesis,G2_table_plan,G3_figure_plan,G4_related_work,G5_ablation_contract,G8_failure_taxonomy,G9_workspace_promotion
ready_gates = G6_calibration_boundary,G7_benchmark_boundary
next_todo = compatibility_dataset_v3_h002_gap_resolution_plan_after_outline_review
```

## Source Reranking Bootstrap CI

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-source-rerank-bootstrap-ci
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/source_reranking_ci/latest/
```

Observed output:

```text
status = h002_source_reranking_bootstrap_ci_ready
n_bootstrap = 1000
bootstrap_unit = source_id/subgraph_id/route_family
unit_count = 2192
score_ids = S0_source_score,S1_Ce_only,S2_source_x_Ce,C1_source_x_shuffled_Ce,C2_source_x_wrong_T_Ce,A1_source_x_G_only,A2_source_x_TG_concat
familywise_unit_scopes = 4
point_metric_mismatch_count = 0
validation_errors = 0
next_todo = h002_source_reranking_ablation_expansion_result_review_after_implementation
```

Boundary: this command only adds CI to frozen source-reranking validation
metrics. It does not fit/tune scores or use official test labels.

## H002 Gap Resolution Pack

Run:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review.py
```

Status: completed, exit 0. Artifact root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/
```

Observed output:

```text
status = h002_gap_resolution_pack_after_outline_review_ready
validation_errors = 0
resolved = claim_thesis,main_result_ci,table_ablation_contract,figure_specs,related_work_novelty_map,failure_taxonomy
workspace_promotion_allowed_now = false
next_todo = compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack
```

Boundary: this closes the internal outline gaps inside the H002 hypothesis
folder. It does not create a new paper workspace and does not allow official
test, SOTA, or leaderboard wording.

## General Framework Gap Synthesis

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-general-framework-gap
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/general_framework_gap/latest/
```

Observed output:

```text
status = h002_general_framework_gap_experiment_synthesis_ready
validation_errors = 0
general_framework_claim = blocked_continue_experiment_stage
support_contact_solved = false
calibrated_pobs_prel_solved = false
normalization_invariant_improvement = false
route_aware_source_wide_generalization = false
next_todo = support_contact_generalization_repair
```

Boundary: this is an experiment-stage synthesis over existing Docker/runtime
artifacts. It does not promote a completed general reliable 3D relation
framework claim.

## Support/Contact Generalization Repair

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-generalization-repair
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/support_contact_generalization_repair/latest/
```

Observed output:

```text
status = h002_support_contact_generalization_repair_ready
validation_errors = 0
candidate_rows = 3178
feature_count = 43
fully_available_feature_count = 43
hard_internal_dev_M4_AUROC = 0.7213559322033898
hard_official_M4_AUROC = 0.0775390596379055
hard_official_M4_balanced_accuracy = 0.18093140339836375
broad_official_support_contact_M4_AUROC = 0.6317116456316851
support_contact_solved = false
selected_path = pose_aware_relabel_abstain_repair_before_more_model_capacity
next_todo = support_contact_generalization_repair_materialization
```

Generated files:

```text
summary.json
feature_gap.csv
predicate_error_summary.csv
class_pair_error_summary.csv
failure_taxonomy.csv
repair_protocol.csv
gate_plan.csv
validation_errors.jsonl
```

Boundary: this repair synthesis does not solve support/contact. It shows that
the current hard route is not limited by missing current `G_e` feature coverage;
instead `standing on` and `lying on` need pose-aware subtype labels, ambiguous
support/contact needs relabel or abstain handling, and `supported by` should stay
as superordinate diagnostic until a subtype decomposition target is available.

## Support/Contact Repair Materialization

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-repair-materialize
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/support_contact_repair_materialization/latest/
```

Observed output:

```text
status = h002_support_contact_generalization_repair_materialization_ready
validation_errors = 0
gate_failures = 1
hard_input_rows = 3178
hard_input_groups = 1589
mixed_class_pairs = 4
main_binary_groups = 20
model_safe_binary_no_class = 40
model_safe_binary_with_class_semantic = 40
model_safe_binary_geometry_only = 40
model_safe_selective_no_class = 3178
single_subtype_groups = 1536
mixed_overflow_groups = 33
metric_rerun_ready = false
next_todo = support_contact_generalization_repair_capacity_decision
```

Generated files:

```text
row_manifest.json
schema_precheck.json
validation_errors.jsonl
gate_failures.jsonl
model_safe_binary_no_class.jsonl
model_safe_binary_with_class_semantic.jsonl
model_safe_binary_geometry_only.jsonl
model_safe_selective_no_class.jsonl
hidden_manifest.jsonl
group_manifest.jsonl
class_pair_quota.csv
pose_proxy_diagnostics.csv
```

Boundary: the materialization is valid, but not metric-ready. After enforcing a
mixed-class-pair criterion, only `40` binary rows over `4` class-pairs remain.
This blocks immediate metric rerun and confirms that the support/contact blocker
is target capacity / class-pair shortcut, not schema or feature availability.

## Support/Contact Capacity Decision

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-capacity-decision
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/support_contact_capacity_decision/latest/
```

Observed output:

```text
status = h002_support_contact_generalization_repair_capacity_decision_ready
validation_errors = 0
binary_rows = 40
mixed_class_pairs = 4
selective_rows = 3178
abstain_rows = 3138
selected_path = freeze_support_contact_as_diagnostic_failure_taxonomy_no_metric_rerun
support_contact_metric_rerun_allowed = false
support_contact_solved_claim_allowed = false
next_todo = pobs_prel_observability_repair
```

Generated files:

```text
summary.json
capacity_options.csv
decision_matrix.csv
paper_boundary.csv
reopen_conditions.csv
class_pair_capacity.csv
validation_errors.jsonl
```

Boundary: support/contact is frozen as diagnostic/failure taxonomy for the
current H002 paper path. Reopening it as a solved route requires independent
pose/observability audit capacity, at least `200` binary rows and `10` mixed
class-pairs after class-pair control, and shortcut probes that cannot solve the
target.

## p_obs / p_rel Observability Repair

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-repair
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_repair/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_repair_ready
validation_errors = 0
asset_observability_label_counts = observable:23062
has_real_negative_or_ambiguous_observability_labels = false
p_rel_calibrated_ECE_10 = 0.22345786060584388
observability_label_queue_rows = 265
pobs_prel_metric_rerun_allowed = false
pobs_prel_calibrated_solved_claim_allowed = false
next_todo = pobs_prel_observability_label_fill
```

Generated files:

```text
summary.json
observability_gap.csv
label_schema.csv
observability_label_queue.jsonl
queue_summary.csv
gate_plan.csv
next_steps.csv
validation_errors.jsonl
```

Boundary: this step creates a visual/mesh observability audit queue, not final
labels or metrics. The current p_obs/p_rel result remains blocked as a
calibrated solved claim because real negative/ambiguous observability labels are
absent and synthetic missing-evidence controls are not final GT.

## p_obs / p_rel Observability Label Fill

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-label-fill
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_labels/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_label_fill_ready
validation_errors = 0
filled_rows = 265
observable_clear = 135
ambiguous_evidence = 126
unobservable_missing_evidence = 4
decision_counts = accept:66,reject:69,abstain:130
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_label_ingestion
```

Boundary: labels were filled by Codex rules with explicit
`codex_filled_not_human_confirmed` provenance. This completes the requested
label fill but does not by itself authorize a metric rerun or calibrated
p_obs/p_rel solved claim.

## p_obs / p_rel Observability Ingestion

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-ingest
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_ingestion/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_label_ingestion_ready
validation_errors = 0
model_safe_qe_view = 265
model_safe_prel_view = 265
hidden_observability_labels = 265
obs_1 = 135
obs_0 = 130
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_schema_audit
```

Generated files:

```text
model_safe_qe_view.jsonl
model_safe_prel_view.jsonl
hidden_observability_labels.jsonl
label_balance.csv
ingestion_manifest.json
validation_errors.jsonl
```

## p_obs / p_rel Observability Schema Audit

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-schema-audit
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_schema_audit/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_schema_audit_ready
validation_errors = 0
blocked_field_hits = 0
qe_rows = 265
prel_rows = 265
hidden_rows = 265
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_metric_gate_decision
```

Boundary: schema separation passed, but metric rerun remains gated because
labels are Codex-filled rather than human-confirmed. The next step is an
explicit metric gate decision.

## p_obs / p_rel Observability Metric Gate

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-metric-gate
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_metric_gate/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_metric_gate_ready
validation_errors = 0
rows = 265
user_review_completed = true
treat_as_user_confirmed_for_diagnostic_metric = true
metric_rerun_allowed_now = true
paper_level_gt_claim_allowed = false
next_todo = pobs_prel_observability_metric_rerun
```

Boundary: the user confirmed the Codex-filled labels for a diagnostic rerun.
The raw label file still records the original Codex provenance, so this does
not create an independently human-authored paper benchmark.

## p_obs / p_rel Observability Metric Rerun

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-metric-runner
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_metric/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_metric_ready
validation_errors = 0
pobs_train = 24340
pobs_eval = 265
prel_train = 4868
prel_eval = 135
p_obs_AUROC = 0.500000
p_obs_ECE_10 = 0.446174
p_rel_AUROC = 0.774704
p_rel_ECE_10 = 0.083819
decision_macro_F1 = 0.331637
diagnostic_metric_pass = false
paper_promotion_pass = false
next_todo = pobs_prel_observability_metric_result_review
```

Interpretation: `p_rel` has useful signal on the user-confirmed observable
subset, but the current `Q_e` does not separate `observable_clear` from
`ambiguous_evidence` or `unobservable_missing_evidence`; median `p_obs` is
`0.955608` for every observability label group. This blocks calibrated p_obs /
p_rel solved-claim wording and points to a Q_e feature/schema insufficiency.

## p_obs / p_rel Observability Metric Review

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-observability-metric-review
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_metric_review/latest/
```

Observed output:

```text
status = h002_pobs_prel_observability_metric_result_review_ready
validation_errors = 0
p_obs_status = failed_observability_gate
p_rel_status = diagnostic_signal_present
selective_decision_status = failed_due_to_no_abstain_behavior
pobs_prel_framework_component_allowed = true
pobs_prel_solved_claim_allowed = false
paper_promotion_pass = false
next_todo = pobs_prel_qe_repair_plan
```

Key cause:

```text
ambiguous_evidence: 126/126 rows still have Q_e sufficient state
unobservable_missing_evidence: 4/4 rows still have Q_e sufficient state
```

Boundary: `p_rel` can be described as a diagnostic reliability signal on
user-confirmed observable rows. `p_obs` / abstention is not solved. The next
step is Q_e feature repair, not another full p_obs/p_rel metric rerun.

## p_obs / p_rel Q_e Repair Plan

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-qe-repair-plan
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_plan/latest/
```

Observed output:

```text
status = h002_pobs_prel_qe_repair_plan_ready
validation_errors = 0
failure_cause = qe_feature_label_mismatch
ambiguous_rows_marked_sufficient = 126
missing_rows_marked_sufficient = 4
pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_materialization
```

Planned repaired Q_e blocks:

```text
Q_e_asset_availability
Q_e_visual_coverage
Q_e_geometry_quality
Q_e_ambiguity
Q_e_state_v2
```

Boundary: this step defines the schema/contract/gates only. It does not yet
materialize repaired Q_e rows or rerun p_obs. The next Docker step should build
`pobs_prel_qe_repair_materialization/latest/`.

## p_obs / p_rel Q_e Repair Materialization

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-qe-repair-materialize
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest/
```

Observed output:

```text
status = h002_pobs_prel_qe_repair_materialization_ready
validation_errors = 0
blocked_field_hits = 0
train_qe_v2_rows = 14604
eval_qe_v2_rows = 265
train_label_counts = observable_clear:4868,ambiguous_evidence:4868,unobservable_missing_evidence:4868
eval_label_counts = observable_clear:135,ambiguous_evidence:126,unobservable_missing_evidence:4
eval_qe_alignment = observable_clear->sufficient:135, ambiguous_evidence->ambiguous:126, unobservable_missing_evidence->missing:4
next_todo = pobs_prel_qe_repair_schema_audit
```

Boundary: eval `Q_e v2` uses audit-proxy diagnostics rather than independent
visual/mesh labels. This is ready for schema audit and p_obs-only diagnostic
smoke testing, but it still does not permit paper-level calibrated p_obs/p_rel
solved wording.

## p_obs / p_rel Q_e Repair Schema Audit

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-qe-repair-schema-audit
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_schema_audit/latest/
```

Observed output:

```text
status = h002_pobs_prel_qe_repair_schema_audit_ready
validation_errors = 0
blocked_field_hits = 0
train_qe_rows = 14604
train_prel_rows = 14604
train_hidden_rows = 14604
eval_qe_rows = 265
eval_prel_rows = 265
eval_hidden_rows = 265
schema_separation = true
row_alignment = true
qe_required_blocks = true
train_label_balance = true
eval_ambiguous_missing_not_sufficient = true
next_todo = pobs_prel_qe_repair_pobs_only_metric
```

Boundary: this opens only a p_obs-only diagnostic metric smoke test. Full
selective-decision rerun and paper-level calibrated p_obs/p_rel solved wording
remain blocked.

## p_obs / p_rel Q_e Repair p_obs-Only Metric

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-qe-repair-pobs-only-metric
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_only_metric/latest/
```

Observed output:

```text
status = h002_pobs_prel_qe_repair_pobs_only_metric_ready
validation_errors = 0
train_rows = 14604
eval_rows = 265
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
p_obs_Brier = 0.004222
p_obs_NLL = 0.051518
abstain_precision = 1.000000
abstain_recall = 1.000000
observable_false_abstain_rate = 0.000000
false_observable_rate = 0.000000
legacy_all_sufficient_AUROC = 0.500000
legacy_all_sufficient_abstain_recall = 0.000000
diagnostic_pass = true
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_pobs_metric_review
```

Boundary: the runner uses repaired `Q_e v2` only and excludes
`qe_v2_diagnostic_source` from model input. Because the eval view is still
audit-proxy diagnostic material, this is a p_obs bottleneck-repair smoke test,
not paper-level calibrated p_obs/p_rel solved evidence.

## p_obs / p_rel Q_e Repair p_obs Metric Review

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-pobs-prel-qe-repair-pobs-metric-review
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_metric_review/latest/
```

Observed output:

```text
status = h002_pobs_prel_qe_repair_pobs_metric_review_ready
validation_errors = 0
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
abstain_recall = 1.000000
direct_Qe_state_AUROC = 1.000000
proxy_shortcut_risk = high
pobs_required_for_core_claim = false
pobs_main_claim_allowed = false
pobs_optional_framework_component = true
full_selective_decision_rerun_now = false
next_todo = h002_core_claim_without_pobs_boundary_update
```

Boundary: the repaired p_obs-only smoke test is a useful bottleneck diagnostic,
but it is not a main paper solved claim. The current H002 core claim should stay
on `C_e` compatibility source reranking. Reopen p_obs/p_rel only with
independent visual/mesh observability labels and a full selective-decision
metric protocol.

## C_e Improvement Path

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-ce-improvement-path
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/ce_improvement_path/latest/
```

Observed output:

```text
status = h002_ce_improvement_path_ready
validation_errors = 0
source_rows_scored = 762888
best_primary_score = I4_calibrated_route_aware_source_x_Ce
calibrated_ce_candidate_pass = true
calibrated_ce_main_promotion = false
richer_ge_support_contact_promotion = false
pobs_prel_reopened = false
```

Primary route point estimate:

```text
S2_current_source_x_Ce @ K=10: Recall 0.513605, Violation 0.072342
I4_calibrated_route_aware_source_x_Ce @ K=10: Recall 0.529478, Violation 0.063573
S2_current_source_x_Ce @ K=20: Recall 0.724490, Violation 0.100487
I4_calibrated_route_aware_source_x_Ce @ K=20: Recall 0.746032, Violation 0.089974
S2_current_source_x_Ce @ K=50: Recall 0.952381, Violation 0.165998
I4_calibrated_route_aware_source_x_Ce @ K=50: Recall 0.960317, Violation 0.151963
```

Boundary: calibrated route-aware `C_e` is a candidate improved score, not a
promoted main score. Promotion requires bootstrap CI and family-wise review.

## C_e Candidate CI / Family Review

Run:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-ce-candidate-ci-family-review
```

Status: completed, exit 0. Output root:

```text
experiments/H002_compatibility_routing/ce_candidate_ci_family_review/latest/
```

Observed output:

```text
status = h002_ce_candidate_ci_family_review_ready
validation_errors = 0
n_bootstrap = 1000
candidate_score = I4_calibrated_route_aware_source_x_Ce
baseline_score = S2_current_source_x_Ce
promote_to_main_score = false
selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
```

K=5:

```text
S2_current_source_x_Ce: Recall@5 0.352608, Violation@5 0.054491
I4_calibrated_route_aware_source_x_Ce: Recall@5 0.358277, Violation@5 0.047554
Delta Recall@5 = +0.005669, 95% CI [-0.006347, 0.017863]
Delta Violation@5 = -0.006937, 95% CI [-0.009130, -0.004834]
```

Promotion decision:

```text
primary_point_K5/K10/K20/K50 = pass
primary_ci_K10/K20 = pass
primary_ci_K5/K50 = fail because Recall CI includes 0
family_no_violation_regression_K5_50 = fail, violation_regression_cells = 5
family_no_double_regression_K5_50 = fail, double_regression_cells = 1
```

Boundary: I4 can be reported as an improved candidate / secondary ablation, but
it should not replace the current main score before family-wise mitigation.
