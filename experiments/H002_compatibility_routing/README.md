# H002 Compatibility Routing Experiment

This folder owns Docker/runtime records for H002:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

The hypothesis framing and paper-facing claim map live in:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/
```

## Current Status

```text
status = h002_ce_candidate_ci_family_review_ready
main_split = official_3DSSG_validation_split
sources = VL-SAT validation predictions, Open3DSG validation predictions
baseline = S0_source_score
primary_score = S2_source_x_Ce
metrics = Recall@K, Violation@K
source_rows_scored = 762888
main_table_rows = 5
source_family_caveat_rows = 3
control_rows = 15
main_validation_table_reviewed = true
paper_draft_insertion_plan_locked = true
pobs_prel_protocol_locked = true
pobs_prel_materialization_ready = true
pobs_prel_selective_metric_pass = true
pobs_prel_paper_promotion_pass = false
pobs_prel_calibration_upgrade_ready = true
pobs_prel_calibration_upgrade_claim_pass = false
h002_standalone_outline_candidate_selected = true
h002_standalone_outline_gap_reviewed = true
main_source_reranking_bootstrap_ci_ready = true
h002_gap_resolution_pack_ready = true
h002_paper_workspace_promotion_decision_ready = true
h002_paper_workspace_initial_sync_ready = true
h002_source_reranking_ablation_expansion_plan_ready = true
h002_source_reranking_ablation_expansion_implementation_ready = true
h002_source_reranking_ablation_expansion_required_score_ids = A1_source_x_G_only,A2_source_x_TG_concat
h002_source_reranking_ablation_expansion_primary_ci_pass = true
h002_source_reranking_ablation_expansion_result_review_ready = true
h002_source_reranking_ablation_expansion_familywise_caveat = violation_stable_recall_mixed
h002_experiment_stage_remaining_gap_review_ready = true
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
h002_support_contact_generalization_repair_next = support_contact_generalization_repair_materialization
h002_support_contact_repair_materialization_ready = true
h002_support_contact_repair_materialization_validation_errors = 0
h002_support_contact_repair_materialization_gate_failures = 1
h002_support_contact_repair_materialization_binary_rows = 40
h002_support_contact_repair_materialization_mixed_class_pairs = 4
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
h002_pobs_prel_qe_repair_eval_alignment = observable_clear:sufficient=135,ambiguous_evidence:ambiguous=126,unobservable_missing_evidence:missing=4
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
h002_pobs_selected_path = demote_pobs_to_optional_diagnostic_keep_core_claim_on_Ce_source_reranking
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
promote_to_new_paper_workspace_now = true
h001_manuscript_edit_now = false
new_top_level_paper_folder_now = false
h002_paper_workspace = paper/h002_compatibility_routing/
official_test_used = false
official_test_benchmark_claim_allowed = false
sota_or_leaderboard_claim_allowed = false
next_todo = h002_route_aware_full_draft_plan_after_section_sync
```

## Claim Boundary

Allowed:

- H002 reranks VL-SAT/Open3DSG validation predictions with `S2_source_x_Ce`.
- `C_e` is fit without `Z_e`; source score is combined only at final reranking.
- Main table uses official 3DSSG validation split.
- Open3DSG is an open-vocabulary source, but quantitative Recall@K uses closed 3DSSG label mapping.
- `Violation@K` is an H002 custom geometry-consistency metric.

Blocked:

- official 3DSSG test result
- leaderboard / SOTA claim
- unconstrained open-set GT evaluation
- uniform improvement across all source/family/K cells
- `support_contact` as solved main route
- H003 embedding as current main contribution
- H001 manuscript integration now
- official-test/SOTA or calibrated p_obs/p_rel solved wording in the H002 paper workspace
- normalization-invariant improvement wording
- completed general reliable 3D relation framework wording

## Folder Map

| Folder | Role |
| --- | --- |
| `scripts/` | executable Docker/runtime scripts |
| `preflight/` | mount and path sanity checks |
| `materialization/` | early route-level candidate materialization |
| `schema_audit/` | early materialization leakage/shortcut audit |
| `splits/` | grouped train/dev/heldout split for internal candidate pool |
| `evaluation/` | internal grouped C_e mechanism evaluation |
| `official_materialization/` | official 3DSSG validation candidate rows |
| `official_schema_audit/` | schema/leakage/shortcut audit for official candidates |
| `official_evaluation/` | official-validation route/family C_e mechanism metrics |
| `source_reranking_materialization/` | source-wide VL-SAT/Open3DSG reranking input views |
| `source_reranking_schema_audit/` | source-wide view separation audit |
| `source_reranking_evaluation/` | paper-facing source reranking metrics |
| `source_reranking_ci/` | bootstrap CI for paper-facing source reranking metrics |
| `source_reranking_sensitivity/` | normalization and no-route G-only sensitivity metrics |
| `ce_improvement_path/` | hard-negative, route-aware, richer-G_e gate, and calibrated-C_e improvement diagnostics |
| `ce_candidate_ci_family_review/` | bootstrap CI, K=5 result, family-wise blocker, and promotion decision for I4 |
| `general_framework_gap/` | experiment-stage synthesis for general-framework promotion gaps |
| `support_contact_generalization_repair/` | support/contact pose-aware relabel/abstain repair protocol synthesis |
| `support_contact_repair_materialization/` | pose-aware support/contact repair rows and capacity gate |
| `support_contact_capacity_decision/` | support/contact capacity decision and paper-boundary lock |
| `support_contact_harder_materialization/` | diagnostic support/contact hard-route rows |
| `support_contact_harder_schema_audit/` | diagnostic support/contact schema/shortcut audit |
| `support_contact_harder_evaluation/` | diagnostic support/contact failure metrics |
| `pobs_prel_materialization/` | p_obs / p_rel selective-decision materialized views |
| `pobs_prel_schema_audit/` | p_obs / p_rel schema/leakage audit |
| `pobs_prel_evaluation/` | p_obs / p_rel selective metrics, calibration, and gate decision |
| `pobs_prel_calibration_upgrade/` | fixed-split calibration, actual asset observability audit, controls, CI, and failure-route connection |
| `pobs_prel_observability_repair/` | visual/mesh observability audit schema and label queue |
| `pobs_prel_observability_labels/` | Codex-filled observability labels for the 265-row audit queue |
| `pobs_prel_observability_ingestion/` | model-safe Q_e / p_rel views plus hidden observability labels |
| `pobs_prel_observability_schema_audit/` | schema separation audit for the ingested observability labels |
| `pobs_prel_observability_metric_gate/` | user-confirmation gate allowing diagnostic metric rerun |
| `pobs_prel_observability_metric/` | diagnostic p_obs / p_rel rerun on the 265-row user-confirmed observability subset |
| `pobs_prel_observability_metric_review/` | result review, Q_e feature-gap audit, and repair plan |
| `pobs_prel_qe_repair_plan/` | repaired Q_e v2 schema, materialization contract, and pass/fail gates |
| `pobs_prel_qe_repair_materialization/` | repaired Q_e v2 train/eval views and hidden observability v2 labels |
| `pobs_prel_qe_repair_schema_audit/` | repaired Q_e v2 schema, leakage, row-alignment, and state-alignment audit |
| `pobs_prel_qe_repair_pobs_only_metric/` | p_obs-only diagnostic smoke test after Q_e v2 repair |
| `pobs_prel_qe_repair_pobs_metric_review/` | p_obs-only result review and claim-boundary decision |

The `latest/` subfolder under each runtime folder is the current materialized run
output. It is not a general archive.

## Paper-Facing Outputs

Main validation table materialized from these runtime outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
```

Latest validation-table review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_main_validation_table_review_after_materialization/
```

Latest paper insertion plan:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review/
```

Latest p_obs / p_rel result review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner/
```

Latest p_obs / p_rel CI/qualitative/failure wording:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review/
```

Latest p_obs / p_rel calibration-upgrade review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/
```

Latest p_obs / p_rel calibration-upgrade runtime:

```text
experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/
```

Latest H002 standalone-outline decision:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan/
```

Latest H002 standalone-outline gap review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision/
```

Latest H002 gap-resolution pack:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/
```

Latest H002 paper-workspace promotion decision:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack/
```

Promoted paper workspace:

```text
paper/h002_compatibility_routing/
```

Latest H002 route-aware paper-workspace sync:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync/
```

Latest source-reranking ablation expansion plan:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/
```

The next Docker/runtime step is to add `A1_source_x_G_only` and
`A2_source_x_TG_concat`, then regenerate absolute metrics and family-wise CI.

Latest source-reranking ablation expansion implementation:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
```

The Docker/runtime step has completed with validation errors `0`; `A1` and
`A2` are now present in source-reranking metrics and bootstrap CI.

Latest source-reranking ablation result review:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/
```

Experiment-stage conclusion: aggregate primary-route evidence supports S2 over
both A1/A2, family-wise Violation is stable, and family-wise Recall is mixed.
Paper promotion remains held until remaining experiment-stage gaps are reviewed.

Latest source-reranking bootstrap CI:

```text
experiments/H002_compatibility_routing/source_reranking_ci/latest/
```

The most important runtime folders are:

```text
source_reranking_materialization/latest/
source_reranking_schema_audit/latest/
source_reranking_evaluation/latest/
source_reranking_ci/latest/
pobs_prel_materialization/latest/
pobs_prel_schema_audit/latest/
pobs_prel_evaluation/latest/
pobs_prel_calibration_upgrade/latest/
general_framework_gap/latest/
```

## Core Runtime Scripts

| Script | Role |
| --- | --- |
| `scripts/materialize_source_reranking_candidates.py` | builds `T_e/G_e`, geometry-only, source-rank, and hidden metric views |
| `scripts/audit_source_reranking_materialization_schema.py` | checks separation between `C_e` inputs, `Z_e`, and hidden labels |
| `scripts/run_source_reranking_metric.py` | fits `C_e`, `A1` geometry-only, and `A2` concat scorers, then evaluates Recall@K / Violation@K |
| `scripts/bootstrap_source_reranking_ci.py` | computes bootstrap CI for `S0`, `S2`, `A1`, `A2`, controls, deltas, and family-wise cells |
| `scripts/run_ce_improvement_path.py` | evaluates hard-negative/structured, route-aware, richer-G_e gate, and calibrated-C_e variants |
| `scripts/review_ce_candidate_ci_family.py` | reviews I4 with bootstrap CI, K=5 result, family blockers, and main-score promotion gate |
| `scripts/official_materialize_candidates.py` | materializes official-validation route-family candidates |
| `scripts/audit_official_materialization_schema.py` | audits official candidate leakage/schema/shortcut risk |
| `scripts/run_official_metric.py` | evaluates semantic-only, geometry-only, concat, and T x G compatibility views |
| `scripts/materialize_support_contact_harder_route.py` | creates diagnostic support/contact hard-route rows |
| `scripts/run_support_contact_harder_metric.py` | evaluates diagnostic support/contact failure route |
| `scripts/materialize_pobs_prel_selective.py` | creates `Q_e`, `p_rel`, and hidden selective-label views |
| `scripts/audit_pobs_prel_materialization_schema.py` | audits p_obs / p_rel schema separation |
| `scripts/run_pobs_prel_selective_metric.py` | evaluates p_obs, p_rel, accept/reject/abstain, and risk-coverage metrics |
| `scripts/run_pobs_prel_calibration_upgrade.py` | runs fixed-split calibration, asset observability audit, controls, CI, and route connection |
| `scripts/repair_pobs_prel_observability.py` | creates p_obs / p_rel observability repair schema and audit queue |
| `scripts/fill_pobs_prel_observability_labels.py` | fills the observability audit queue with Codex labels and explicit non-human provenance |
| `scripts/ingest_pobs_prel_observability_labels.py` | builds model-safe Q_e / p_rel views and hidden observability labels |
| `scripts/audit_pobs_prel_observability_schema.py` | audits label separation, blocked fields, and row alignment for observability views |
| `scripts/decide_pobs_prel_observability_metric_gate.py` | records user confirmation and opens the diagnostic observability metric gate |
| `scripts/run_pobs_prel_observability_metric.py` | trains on the frozen internal p_obs/p_rel protocol and evaluates the user-confirmed observability subset |
| `scripts/review_pobs_prel_observability_metric.py` | reviews the diagnostic rerun, freezes p_obs failure / p_rel signal, and writes the Q_e repair plan |
| `scripts/plan_pobs_prel_qe_repair.py` | turns the p_obs failure review into a Q_e v2 schema, materialization contract, and next implementation plan |
| `scripts/materialize_pobs_prel_qe_repair.py` | materializes repaired Q_e v2 train/eval views and hidden observability v2 labels |
| `scripts/audit_pobs_prel_qe_repair_schema.py` | audits repaired Q_e v2 schema separation, required blocks, row alignment, and state alignment |
| `scripts/run_pobs_prel_qe_repair_pobs_only_metric.py` | evaluates repaired Q_e v2 with a p_obs-only diagnostic smoke test |
| `scripts/review_pobs_prel_qe_repair_pobs_metric.py` | reviews the p_obs-only diagnostic pass and demotes p_obs from the core claim |
| `scripts/synthesize_general_framework_gap.py` | synthesizes remaining gates for general-framework promotion |
| `scripts/synthesize_support_contact_generalization_repair.py` | synthesizes support/contact pose-aware relabel/abstain repair protocol |
| `scripts/materialize_support_contact_repair.py` | materializes mixed-class-pair support/contact repair rows and gate diagnostics |
| `scripts/decide_support_contact_capacity.py` | decides whether repaired support/contact can proceed to metric rerun |

## Archive

Historical H002 hypothesis-stage files were moved to:

```text
archive/hypothesis_records/hypothesis/H002_factorized-relation-confidence_cleanup_20260703/
```

Use the active hypothesis `paper_claim_core.md` for the current score/code/artifact map.
