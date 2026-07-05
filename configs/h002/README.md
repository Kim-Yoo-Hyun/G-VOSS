# H002 Docker Config

This folder owns Docker configuration for H002 compatibility-routing runtime.

## Current Status

```text
status = h002_ce_candidate_ci_family_review_ready
paper_metric_ready = true_validation_only_with_caveats
paper_table_draft_allowed = true
paper_table_skeleton_ready = true
paper_table_skeleton_reviewed = true
bounded_mechanism_evidence_only = true
principled_design_gap_plan_ready = true
selected_gap = harder_support_contact_route
support_contact_harder_route_protocol_ready = true
support_contact_harder_route_source_inventory_ready = true
support_contact_harder_route_materialization_plan_ready = true
support_contact_harder_route_docker_materialization_ready = true
support_contact_harder_route_schema_shortcut_audit_ready = true_with_shortcut_warnings
support_contact_harder_route_metric_protocol_ready = true
support_contact_harder_route_train_eval_alignment_ready = true
support_contact_harder_route_train_eval_feature_parity = ready_with_derived_proxy_mappings
support_contact_harder_route_metric_runner_ready = true
support_contact_harder_route_metric_expectation_passed = false
source_reranking_materialization_run = true
source_reranking_materialization_ready = true
source_reranking_materialization_validation_errors = 0
source_reranking_total_rows = 762888
source_reranking_primary_success_family_rows = 254296
source_reranking_schema_audit_run = true
source_reranking_schema_audit_ready = true
source_reranking_schema_audit_validation_errors = 0
source_reranking_blocked_field_hits = 0
source_reranking_metric_protocol_freeze_ready = true
source_reranking_metric_protocol_validation_errors = 0
source_reranking_primary_score = S2_source_x_Ce
source_reranking_metric_runner_ready = true
source_reranking_metric_runner_validation_errors = 0
source_reranking_source_rows_scored = 762888
source_reranking_internal_train_rows = 4868
source_reranking_bootstrap_ci_ready = true
source_reranking_bootstrap_ci_validation_errors = 0
source_reranking_bootstrap_ci_samples = 1000
source_reranking_bootstrap_ci_point_mismatch_count = 0
source_reranking_metric_result_review_ready = true
source_reranking_validation_evidence = positive
source_reranking_negative_recall_cells = 3
source_reranking_claim_boundary_locked = true
source_reranking_table_role = main_validation_benchmark
source_reranking_validation_table_skeleton_ready = true
source_reranking_validation_table_primary_rows = 5
source_reranking_validation_table_control_rows = 15
source_reranking_validation_table_caveat_rows = 3
source_reranking_validation_table_review_ready = true
source_reranking_validation_table_position = main_validation_benchmark
test_benchmark_table_required = true
test_benchmark_ready_now = false
test_benchmark_preflight_ready = true_blocked
canonical_test_file_exists = false
validation_alias_test_candidates = 2
official_test_source_rows = 0
test_benchmark_source_resolution_ready = true_blocked
accepted_official_eval_server_confirmed = false
independent_relation_test_label_confirmed = false
scan_level_3rscan_test_split_exists = true
scan_level_split_is_sufficient_for_h002 = false
relation_test_source_predictions_available = false
external_provenance_request_ready = true
external_response_ingestion_ready = true
external_response_found = false
official_validation_standard_confirmed = false
validation_only_position_lock_ready = true
validation_only_position = superseded_by_main_validation_path_decision
post_validation_position_path_decision_ready = true
main_validation_claim_allowed = true
main_validation_table_allowed = true
main_validation_table_locked = true
main_validation_table_materialized = true
main_validation_table_reviewed = true
paper_draft_insertion_plan_locked = true
standalone_outline_gap_review_ready = true
h002_gap_resolution_pack_ready = true
h002_gap_resolution_pack_validation_errors = 0
pobs_prel_calibration_upgrade_ready = true
pobs_prel_calibration_upgrade_claim_pass = false
h002_paper_workspace_promotion_decision_ready = true
h002_paper_workspace_initial_sync_ready = true
new_paper_workspace_created = true
h002_paper_workspace = paper/h002_compatibility_routing/
main_validation_table_rows = 5
main_validation_table_caveat_rows = 3
main_validation_table_control_rows = 15
official_test_benchmark_claim_allowed = false
open3dsg_source_boundary = open_vocabulary_source_closed_vocabulary_3dssg_mapping
h003_embedding_extension_in_main_claim_now = false
h003_embedding_extension_future_optional = true
h002_source_reranking_ablation_expansion_plan_ready = true
h002_source_reranking_ablation_expansion_implementation_ready = true
source_reranking_ablation_expansion_primary_ci_pass = true
h002_source_reranking_ablation_expansion_result_review_ready = true
source_reranking_ablation_expansion_familywise_caveat = violation_stable_recall_mixed
h002_source_reranking_sensitivity_ready = true
h002_source_reranking_sensitivity_validation_errors = 0
h002_source_reranking_sensitivity_rows = 762888
h002_source_reranking_sensitivity_decision = minmax_main_allowed_with_raw_product_sensitivity_and_rankpct_caveat
h002_no_route_g_only_sensitivity_passed = true
h002_ce_improvement_path_ready = true
h002_ce_improvement_path_validation_errors = 0
h002_ce_improvement_source_rows_scored = 762888
h002_ce_improvement_best_primary_score = I4_calibrated_route_aware_source_x_Ce
h002_ce_improvement_calibrated_candidate_pass = true
h002_ce_improvement_calibrated_main_promotion = false
h002_ce_improvement_support_contact_promotion = false
h002_ce_candidate_ci_family_review_ready = true
h002_ce_candidate_ci_family_review_validation_errors = 0
h002_ce_candidate_ci_family_review_bootstrap_samples = 1000
h002_ce_candidate_ci_family_review_promote_to_main_score = false
h002_ce_candidate_ci_family_review_selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
h002_ce_candidate_ci_family_review_k5_s2_recall_violation = 0.352608,0.054491
h002_ce_candidate_ci_family_review_k5_i4_recall_violation = 0.358277,0.047554
h002_ce_candidate_ci_family_review_violation_regression_cells = 5
h002_ce_candidate_ci_family_review_double_regression_cells = 1
h002_general_framework_gap_synthesis_ready = true
h002_general_framework_gap_validation_errors = 0
h002_general_framework_claim = blocked_continue_experiment_stage
h002_support_contact_solved = false
h002_calibrated_pobs_prel_solved = false
h002_normalization_invariant_improvement = false
h002_route_aware_source_wide_generalization = false
h002_support_contact_generalization_repair_ready = true
h002_support_contact_generalization_repair_validation_errors = 0
h002_support_contact_generalization_repair_selected_path = pose_aware_relabel_abstain_repair_before_more_model_capacity
h002_support_contact_repair_materialization_ready = true
h002_support_contact_repair_materialization_validation_errors = 0
h002_support_contact_repair_materialization_gate_failures = 1
h002_support_contact_repair_metric_rerun_ready = false
h002_support_contact_capacity_decision_ready = true
h002_support_contact_capacity_decision_validation_errors = 0
h002_support_contact_capacity_decision_selected_path = freeze_support_contact_as_diagnostic_failure_taxonomy_no_metric_rerun
h002_support_contact_metric_rerun_allowed = false
h002_pobs_prel_observability_repair_ready = true
h002_pobs_prel_observability_repair_validation_errors = 0
h002_pobs_prel_observability_queue_rows = 265
h002_pobs_prel_observability_label_fill_ready = true
h002_pobs_prel_observability_label_fill_validation_errors = 0
h002_pobs_prel_observability_label_fill_rows = 265
h002_pobs_prel_observability_label_counts = observable_clear:135,ambiguous_evidence:126,unobservable_missing_evidence:4
h002_pobs_prel_observability_ingestion_ready = true
h002_pobs_prel_observability_ingestion_validation_errors = 0
h002_pobs_prel_observability_ingestion_rows = 265
h002_pobs_prel_observability_schema_audit_ready = true
h002_pobs_prel_observability_schema_audit_validation_errors = 0
h002_pobs_prel_observability_schema_audit_blocked_field_hits = 0
h002_pobs_prel_observability_labels_human_confirmed = false
h002_pobs_prel_observability_metric_gate_ready = true
h002_pobs_prel_observability_metric_gate_validation_errors = 0
h002_pobs_prel_observability_user_review_completed = true
h002_pobs_prel_observability_metric_rerun_allowed = true
h002_pobs_prel_observability_metric_ready = true
h002_pobs_prel_observability_metric_validation_errors = 0
h002_pobs_prel_observability_metric_diagnostic_pass = false
h002_pobs_prel_observability_metric_p_obs_auroc = 0.500000
h002_pobs_prel_observability_metric_p_rel_auroc = 0.774704
h002_pobs_prel_observability_metric_decision_macro_f1 = 0.331637
h002_pobs_prel_observability_metric_result_review_ready = true
h002_pobs_prel_observability_metric_result_review_validation_errors = 0
h002_pobs_status = failed_observability_gate
h002_prel_status = diagnostic_signal_present
h002_selective_decision_status = failed_due_to_no_abstain_behavior
h002_qe_repair_needed = true
h002_pobs_prel_qe_repair_plan_ready = true
h002_pobs_prel_qe_repair_plan_validation_errors = 0
h002_qe_repair_failure_cause = qe_feature_label_mismatch
h002_qe_repair_ambiguous_rows_marked_sufficient = 126
h002_qe_repair_missing_rows_marked_sufficient = 4
h002_pobs_prel_qe_repair_materialization_ready = true
h002_pobs_prel_qe_repair_materialization_validation_errors = 0
h002_pobs_prel_qe_repair_materialization_train_rows = 14604
h002_pobs_prel_qe_repair_materialization_eval_rows = 265
h002_pobs_prel_qe_repair_materialization_blocked_field_hits = 0
h002_pobs_prel_qe_repair_schema_audit_ready = true
h002_pobs_prel_qe_repair_schema_audit_validation_errors = 0
h002_pobs_prel_qe_repair_schema_audit_blocked_field_hits = 0
h002_pobs_prel_qe_repair_pobs_only_metric_allowed = true
h002_pobs_prel_qe_repair_full_selective_rerun_allowed = false
h002_pobs_prel_qe_repair_pobs_only_metric_ready = true
h002_pobs_prel_qe_repair_pobs_only_metric_validation_errors = 0
h002_pobs_prel_qe_repair_pobs_only_metric_diagnostic_pass = true
h002_pobs_prel_qe_repair_pobs_auroc = 1.000000
h002_pobs_prel_qe_repair_pobs_ece_10 = 0.049266
h002_pobs_prel_qe_repair_abstain_recall = 1.000000
h002_pobs_prel_qe_repair_observable_false_abstain = 0.000000
h002_pobs_prel_qe_repair_pobs_metric_review_ready = true
h002_pobs_prel_qe_repair_pobs_metric_review_validation_errors = 0
h002_pobs_proxy_shortcut_risk = high
h002_pobs_required_for_core_claim = false
h002_pobs_main_claim_allowed = false
h002_pobs_optional_framework_component = true
h002_pobs_full_selective_decision_rerun_now = false
h002_pobs_prel_metric_rerun_allowed = completed_diagnostic_only
h002_pobs_prel_calibrated_solved_claim_allowed = false
h002_method_principle = natural_and_principled_for_scoped_problem
h002_relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
h002_general_reliable_3d_relation_framework = not_yet_validated
h002_paper_framework_direction = relation_aware_evidence_routing
h002_validated_mechanism_claim = predicate_geometry_compatibility_route
h002_validated_mechanism_relations = relative_vertical,size_relative
h002_validated_main_score = S2_current_source_x_Ce
h002_i4_position = secondary_candidate_ablation_not_main_score
h002_claim_hierarchy_and_route_protocol_ready = true
h002_paper_section_sync_after_protocol_freeze_ready = true
h002_next_todo_type = full_draft_plan_not_metric_run
checkpoint_reproduction_is_sufficient_for_test_recall = false
prediction_only_test_scan_export_is_sufficient_for_test_recall = false
final_paper_result_promotion = validation_table_candidate_only
next_todo = h002_route_aware_full_draft_plan_after_section_sync
```

## Planned Services

| Service | Role |
| --- | --- |
| `h002-protocol-check` | verify mounts, artifact statuses, and output roots |
| `h002-materialize-routes` | regenerate promoted route rows and model-safe/hidden manifests |
| `h002-materialization-schema-audit` | audit materialized rows for schema leakage, shortcut risk, and split-readiness |
| `h002-grouped-split` | create internal train/dev/heldout split by `cv_group_id` without running metrics |
| `h002-shortcut-audit` | run leakage, shortcut, wrong-T, and shuffled-G audits |
| `h002-grouped-eval` | run grouped-holdout route metrics and controls |
| `h002-official-materialize-candidates` | materialize official validation candidates without metrics |
| `h002-official-materialization-schema-audit` | audit official candidate materialization for leakage, shortcut risk, label balance, and control readiness |
| `h002-official-metric-runner` | run official validation metrics after protocol freeze |
| `h002-support-contact-hard-materialize` | richer support/contact hard-route materializer; completed once, no metrics |
| `h002-support-contact-hard-schema-audit` | audit richer support/contact hard-route materialization for schema leakage, shortcut risk, and control readiness; completed once, no metrics |
| `h002-support-contact-hard-metric-runner` | run support/contact hard-route metrics after train/eval alignment; completed once, not promoted |
| `h002-source-rerank-materialize` | materialize full VL-SAT/Open3DSG source prediction universe for downstream source reranking; completed once, no metrics |
| `h002-source-rerank-schema-audit` | audit source-reranking materialization view separation, aggregation, and control readiness; completed once, no metrics |
| `h002-source-rerank-metric-runner` | compute frozen source-reranking `Recall@K`, `Violation@K`, and controls; completed once |
| `h002-source-rerank-bootstrap-ci` | compute bootstrap CI for frozen source-reranking `Recall@K`, `Violation@K`, and `S2-S0` deltas; completed once |
| `h002-source-rerank-sensitivity` | run normalization and no-route G-only source-reranking sensitivity; completed once |
| `h002-ce-improvement-path` | run hard-negative/structured, route-aware, richer-G_e gate, and calibrated-C_e diagnostics; completed once |
| `h002-ce-candidate-ci-family-review` | run bootstrap CI, K=5 result, family blocker review, and promotion gate for I4; completed once |
| `h002-general-framework-gap` | synthesize experiment-stage gates for general-framework promotion; completed once |
| `h002-support-contact-generalization-repair` | synthesize pose-aware relabel/abstain repair gates for support/contact; completed once |
| `h002-support-contact-repair-materialize` | materialize mixed-class-pair support/contact repair rows and capacity gate; completed once |
| `h002-support-contact-capacity-decision` | decide support/contact metric rerun capacity and paper boundary; completed once |
| `h002-pobs-prel-observability-repair` | create real-observability label schema and visual/mesh audit queue; completed once |
| `h002-pobs-prel-materialize` | materialize `Q_e`, `p_rel`, and hidden selective labels; completed once |
| `h002-pobs-prel-schema-audit` | audit p_obs/p_rel schema separation; completed once |
| `h002-pobs-prel-metric-runner` | evaluate p_obs/p_rel selective stress test and calibration; completed once |
| `h002-pobs-prel-calibration-upgrade` | run fixed-split calibration, asset observability audit, CI, controls, and failure-route connection; completed once |
| `h002-pobs-prel-observability-label-fill` | fill the 265-row visual/mesh observability queue with Codex labels; completed once |
| `h002-pobs-prel-observability-ingest` | ingest filled observability labels into model-safe and hidden views; completed once |
| `h002-pobs-prel-observability-schema-audit` | audit model-safe / hidden separation for observability labels; completed once |
| `h002-pobs-prel-observability-metric-gate` | record user-confirmation and allow diagnostic p_obs/p_rel observability metric rerun; completed once |
| `h002-pobs-prel-observability-metric-runner` | run diagnostic p_obs/p_rel metrics on the 265-row user-confirmed observability subset; completed once |
| `h002-pobs-prel-observability-metric-review` | review the diagnostic rerun and freeze Q_e repair as the next step; completed once |
| `h002-pobs-prel-qe-repair-plan` | define repaired Q_e v2 schema, materialization contract, and gates; completed once |
| `h002-pobs-prel-qe-repair-materialize` | materialize repaired Q_e v2 train/eval views and hidden observability v2 labels; completed once |
| `h002-pobs-prel-qe-repair-schema-audit` | audit repaired Q_e v2 leakage, required blocks, row alignment, and state alignment; completed once |
| `h002-pobs-prel-qe-repair-pobs-only-metric` | run repaired Q_e v2 p_obs-only diagnostic smoke test; completed once |
| `h002-pobs-prel-qe-repair-pobs-metric-review` | review p_obs-only diagnostic pass and freeze p_obs claim boundary; completed once |

## Boundary

`Dockerfile` and `compose.yaml` currently implement `h002-protocol-check`,
`h002-materialize-routes`, `h002-materialization-schema-audit`,
`h002-grouped-split`, `h002-grouped-eval`,
`h002-official-materialize-candidates`,
`h002-official-materialization-schema-audit`, `h002-official-metric-runner`,
`h002-support-contact-hard-materialize`,
`h002-support-contact-hard-schema-audit`,
`h002-support-contact-hard-metric-runner`,
`h002-source-rerank-materialize`, `h002-source-rerank-schema-audit`, and
`h002-source-rerank-metric-runner`, `h002-source-rerank-bootstrap-ci`,
`h002-source-rerank-sensitivity`, `h002-general-framework-gap`,
`h002-support-contact-generalization-repair`,
`h002-support-contact-repair-materialize`,
`h002-support-contact-capacity-decision`,
`h002-pobs-prel-observability-repair`, `h002-pobs-prel-materialize`,
`h002-pobs-prel-schema-audit`,
`h002-pobs-prel-metric-runner`, `h002-pobs-prel-calibration-upgrade`,
`h002-pobs-prel-observability-label-fill`,
`h002-pobs-prel-observability-ingest`,
`h002-pobs-prel-observability-schema-audit`,
`h002-pobs-prel-observability-metric-gate`,
`h002-pobs-prel-observability-metric-runner`,
`h002-pobs-prel-observability-metric-review`, and
`h002-pobs-prel-qe-repair-plan`,
`h002-pobs-prel-qe-repair-materialize`, and
`h002-pobs-prel-qe-repair-schema-audit`, and
`h002-pobs-prel-qe-repair-pobs-only-metric`, and
`h002-pobs-prel-qe-repair-pobs-metric-review`.

Docker preflight passed with exit 0. Route materialization also passed with exit
0 and wrote row-level runtime outputs under:

```text
experiments/H002_compatibility_routing/materialization/latest/
```

Materialization schema audit also passed with exit 0 and wrote audit outputs under:

```text
experiments/H002_compatibility_routing/schema_audit/latest/
```

Grouped split protocol also passed with exit 0 and wrote split outputs under:

```text
experiments/H002_compatibility_routing/splits/latest/
```

Official metric result review, official metric claim-boundary lock, source-reranking result review, source-reranking claim-boundary lock, p_obs/p_rel stress-test review, p_obs/p_rel calibration-upgrade review, source-reranking CI, and H002 gap-resolution artifacts now exist under the H002 hypothesis folder. Do not promote p_obs/p_rel as a calibrated quantitative paper result because the calibration-upgrade gate did not pass.

Grouped evaluation protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/
```

Grouped evaluation runner has passed and wrote runtime metrics under:

```text
experiments/H002_compatibility_routing/evaluation/latest/
```

Relative-vertical failure analysis has passed, and `h002-grouped-eval` feature
extraction has been repaired so compatibility features read explicit raw
geometry paths rather than suffix-matching availability-mask fields. Repaired
grouped-eval claim-boundary review and official validation/source-inventory
planning have also passed.
`Z_e` and `Q_e` remain outside the main `C_e` model unless a separate `p_rel` /
`p_obs` protocol is created.

Official source inventory now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
```

The previous config-level blocker was defining the official candidate
materialization protocol before adding new Docker commands.

Official candidate materialization protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
```

`h002-official-materialize-candidates` has been added to `configs/h002/compose.yaml`
and has completed once with exit 0. `h002-official-materialization-schema-audit`
has also completed once with exit 0 and wrote:

```text
experiments/H002_compatibility_routing/official_schema_audit/latest/
```

The audit found `0` schema violations, `0` blocked field hits, `0` runtime
validation errors, and `0` control-readiness blockers. It also found one
claim-boundary caveat: `support_contact` `predicate_x_class_pair` majority
accuracy `0.993707`. The official metric runner and subsequent result-review
stages have completed, but no final paper metric has been promoted.

Official metric protocol freeze now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
```

Support/contact hard-route source inventory now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol/
```

This confirms that official validation support/contact source assets are
available for a richer `G_e` materializer, but the current support/contact result
is still not a final paper result because `predicate_x_class_pair` shortcut risk
remains high.

Support/contact hard-route materialization plan now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory/
```

It plans a future `h002-support-contact-hard-materialize` Docker service and
runtime output root:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```

This service has now been implemented and completed once with exit 0. Runtime
outputs live under:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```

It wrote `3178` richer support/contact rows, `1589` group rows, `43` `G_e`
features, and `0` validation errors. The next work is schema/shortcut audit, not
metric execution.

`h002-support-contact-hard-schema-audit` has now completed once with exit 0 and
wrote:

```text
experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest/
```

The audit found `0` validation errors, `0` blocked field hits, full view
alignment, `7/7` controls ready, and `3` shortcut warnings. The high-risk
`predicate x class-pair` warning blocks solved-family wording but does not block
metric protocol freeze.

Support/contact hard-route metric protocol freeze now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit/
```

The support/contact hard-route metric runner service has now been added after
train/eval feature alignment. The earlier blocker was that official validation
had `43` canonical `G_e` features while the available train reference used a
different prefixed `63`-feature schema.

Support/contact hard-route train/eval alignment now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze/
```

`h002-support-contact-hard-metric-runner` has now completed once with exit 0 and
wrote:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
```

It used the alignment artifact's `runner_input_contract.json`, fit only on
`internal_train`, selected only on `internal_dev`, and kept official validation
eval-only. The run is not promoted because official validation `M4` AUROC is
`0.077539` and wrong-`T` AUROC is `0.922461`; result review is next.

`h002-official-metric-runner` has now completed once with exit 0 and wrote under:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

It treats official validation rows as eval-only and does not use official test.
Official metric result review, claim-boundary lock, table skeleton, table review,
gap planning, support/contact hard-route protocol, source inventory,
materialization planning, and Docker materialization have completed. The next
work is schema/shortcut audit for richer support/contact `G_e`.

Source-reranking materialization has also completed under:

```text
experiments/H002_compatibility_routing/source_reranking_materialization/latest/
```

It wrote `762888` source-family rows across VL-SAT and Open3DSG official
validation source predictions. The runtime view separation is:

```text
model_safe_ce_view.jsonl = T_e + G_e only
source_rank_view.jsonl = Z_e reranking-only
hidden_metric_manifest.jsonl = GT/violation metric-only
validation_errors.jsonl = 0 rows
```

No source reranking metric, official test, or paper result was produced. The
source-reranking materialization schema audit has also completed under:

```text
experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
```

The audit found candidate-id alignment pass, `T_e + G_e` only `C_e` view,
blocked `C_e` feature hits `0`, `Z_e` reranking-only separation, hidden
metric-only separation, balanced primary success families, and support/contact
diagnostic exclusion. No metric was run.

Source-reranking metric protocol freeze has now completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit/
```

Frozen summary:

```text
primary_score = S2_source_x_Ce
K_grid = 5,10,20,50,100
primary_success_families = relative_vertical,size_relative
support_contact = diagnostic excluded
validation_errors = 0
official_test_used = false
metric_runner_executed = false
```

The source-reranking metric runner has now completed under:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

It scored `762888` source rows, fit `C_e` only on `4868` internal-train rows,
used no official test, and wrote `0` validation errors. The next H002
config-level step was result review, not final paper promotion.

Source-reranking result review has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner/
```

It marks the validation evidence as positive, but keeps paper promotion blocked
until claim-boundary lock. The next H002 config-level step is claim-boundary
lock.

Test benchmark source resolution has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight/
```

This gate confirms that no H002 test benchmark Docker service should be opened
yet. The 3RScan scan-level test split exists, but accepted 3DSSG relation-test
evaluation/server provenance and exact test source predictions are not
confirmed. Keep validation source-reranking output as appendix/secondary
evidence until external provenance is resolved.

External provenance request packet has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution/
```

No Docker test benchmark service should be opened from this config until an
official response or documentation is ingested. Checkpoint reproduction and
prediction-only test-scan export remain insufficient for test `Recall@K`.

External response ingestion has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request/
```

No response/provenance artifact was found. This config must keep H002 test
benchmark services closed and treat validation source-reranking as
appendix/secondary analysis until official provenance is provided.

Validation-only position lock has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response/
```

This config remains closed to official-test services. Current H002 metrics are
validation-only custom-protocol evidence. Open3DSG source claims must include
the open-vocabulary source / closed-vocabulary 3DSSG evaluation boundary.

Post-validation path decision has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision/
```

H002 now treats official 3DSSG validation as the main comparative split. Config
services for official test remain closed; the next step is table/claim wording
lock, not a new metric run.

Main validation claim/table lock has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision/
```

Compact table materialization from existing validation artifacts has since
completed. Do not open an official-test service.

Main validation table materialization has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
```

Table review has since completed. Do not add a new metric service or
official-test service from this state.

Main validation table review has also completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization/
```

Paper draft insertion planning was the next step at that time, not a new Docker
service. It has since completed. Keep official-test services closed unless
independent relation-test labels or an accepted evaluation server are confirmed.

Paper draft insertion planning has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review/
```

The source-reranking ablation expansion implementation has completed. The
Docker/runtime path now adds `A1_source_x_G_only` and `A2_source_x_TG_concat`,
then regenerates absolute control/ablation metrics and family-wise CI.

The ablation expansion plan is frozen under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/
```

The implementation artifact is:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
```

The result-review artifact is:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/
```

Historical H002 hypothesis-stage files were moved to:

```text
archive/hypothesis_records/hypothesis/H002_factorized-relation-confidence_cleanup_20260703/
```

Use the active H002 `paper_claim_core.md` for the current score/code/artifact map.

H001 artifacts must be mounted read-only if referenced.
