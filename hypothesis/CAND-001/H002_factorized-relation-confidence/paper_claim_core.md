# H002 Paper Claim Core

## Current Claim

H002 is a factorized reliability/reranking layer for 3D Scene Graph relations.
It does not replace VL-SAT or Open3DSG. It reranks their validation predictions
with a compatibility score:

```text
T_e = predicate / relation-family semantic content
G_e = predicate-independent geometry evidence
Z_e = source confidence, score, rank
C_e = compatibility(T_e, G_e)
Q_e = observability / evidence quality
S2(e) = normalized_source_score(Z_e) * C_e
optional p_obs = P(evidence is sufficient to decide | Q_e)
optional p_rel = P(relation is reliable | observable evidence, Z_e, C_e)
```

Main paper-facing score:

```text
S0_source_score = source confidence baseline
S2_source_x_Ce = source score combined with C_e after C_e is computed from T_e and G_e
```

## Paper-Facing Result

Current stage:

```text
current_gate = h002_ce_candidate_ci_family_review_ready
current_extension_gate = h002_ce_candidate_ci_family_review_ready
paper_claim_boundary_locked_after_sensitivity = true
experiment_stage_gap_review_result = paper_claim_possible_if_scoped
normalization_no_route_geometry_sensitivity_result = no_route_g_only_passed_raw_product_supported_rankpct_low_k_caveat
method_principle = natural_and_principled_for_scoped_problem
relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
general_reliable_3d_relation_framework = not_yet_validated
locked_claim = validation_level_comparison_route_source_reranking
comparison_route_main_claim_allowed = true
relation_aware_framework_partially_validated = true
general_reliable_framework_completed_result = false
paper_framework_direction = relation_aware_evidence_routing
framework_claim_role = broad_problem_and_design_framework
validated_mechanism_claim = predicate_geometry_compatibility_route
validated_mechanism_relations = relative_vertical,size_relative
validated_main_score = S2_current_source_x_Ce
i4_position = secondary_candidate_ablation_not_main_score
route_taxonomy_status = claim_hierarchy_and_protocol_frozen
claim_hierarchy_and_route_protocol_ready = true
paper_section_sync_after_protocol_freeze_ready = true
general_framework_gap_synthesis_ready = true
general_framework_claim = blocked_continue_experiment_stage
support_contact_solved = false
calibrated_pobs_prel_solved = false
pobs_prel_observability_label_fill_ready = true
pobs_prel_observability_ingestion_ready = true
pobs_prel_observability_schema_audit_ready = true
pobs_prel_observability_rows = 265
pobs_prel_observability_label_counts = observable_clear:135,ambiguous_evidence:126,unobservable_missing_evidence:4
pobs_prel_observability_blocked_field_hits = 0
pobs_prel_observability_labels_human_confirmed = false
pobs_prel_observability_user_review_completed = true
pobs_prel_observability_metric_gate_ready = true
pobs_prel_observability_metric_ready = true
pobs_prel_observability_metric_validation_errors = 0
pobs_prel_observability_metric_p_obs_auroc = 0.500000
pobs_prel_observability_metric_p_rel_auroc = 0.774704
pobs_prel_observability_metric_decision_macro_f1 = 0.331637
pobs_prel_observability_metric_diagnostic_pass = false
pobs_prel_observability_metric_result_review_ready = true
pobs_prel_observability_metric_result_review_validation_errors = 0
pobs_status = failed_observability_gate
prel_status = diagnostic_signal_present
selective_decision_status = failed_due_to_no_abstain_behavior
qe_repair_needed = true
pobs_prel_qe_repair_plan_ready = true
pobs_prel_qe_repair_plan_validation_errors = 0
qe_repair_failure_cause = qe_feature_label_mismatch
qe_repair_blocks = Q_e_asset_availability,Q_e_visual_coverage,Q_e_geometry_quality,Q_e_ambiguity,Q_e_state_v2
pobs_prel_qe_repair_materialization_ready = true
pobs_prel_qe_repair_materialization_validation_errors = 0
pobs_prel_qe_repair_materialization_train_rows = 14604
pobs_prel_qe_repair_materialization_eval_rows = 265
pobs_prel_qe_repair_materialization_blocked_field_hits = 0
pobs_prel_qe_repair_eval_alignment = observable_clear:sufficient=135,ambiguous_evidence:ambiguous=126,unobservable_missing_evidence:missing=4
pobs_prel_qe_repair_schema_audit_ready = true
pobs_prel_qe_repair_schema_audit_validation_errors = 0
pobs_prel_qe_repair_schema_audit_blocked_field_hits = 0
pobs_prel_qe_repair_pobs_only_metric_allowed = true
pobs_prel_qe_repair_full_selective_rerun_allowed = false
pobs_prel_qe_repair_pobs_only_metric_ready = true
pobs_prel_qe_repair_pobs_only_metric_validation_errors = 0
pobs_prel_qe_repair_pobs_only_metric_diagnostic_pass = true
pobs_prel_qe_repair_pobs_auroc = 1.000000
pobs_prel_qe_repair_pobs_ece_10 = 0.049266
pobs_prel_qe_repair_abstain_recall = 1.000000
pobs_prel_qe_repair_observable_false_abstain = 0.000000
pobs_prel_qe_repair_legacy_all_sufficient_auroc = 0.500000
pobs_prel_qe_repair_legacy_all_sufficient_abstain_recall = 0.000000
pobs_prel_qe_repair_pobs_metric_review_ready = true
pobs_prel_qe_repair_pobs_metric_review_validation_errors = 0
pobs_proxy_shortcut_risk = high
pobs_required_for_core_claim = false
pobs_main_claim_allowed = false
pobs_optional_framework_component = true
pobs_full_selective_decision_rerun_now = false
pobs_selected_path = demote_pobs_to_optional_diagnostic_keep_core_claim_on_Ce_source_reranking
pobs_prel_metric_rerun_allowed_now = completed_diagnostic_only
ce_improvement_path_ready = true
ce_improvement_path_validation_errors = 0
ce_improvement_source_rows_scored = 762888
ce_improvement_best_primary_score = I4_calibrated_route_aware_source_x_Ce
ce_improvement_calibrated_candidate_pass = true
ce_improvement_calibrated_main_promotion = false
ce_improvement_support_contact_promotion = false
ce_candidate_ci_family_review_ready = true
ce_candidate_ci_family_review_validation_errors = 0
ce_candidate_ci_family_review_bootstrap_samples = 1000
ce_candidate_ci_family_review_promote_to_main_score = false
ce_candidate_ci_family_review_selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
ce_candidate_ci_family_review_k5_s2_recall_violation = 0.352608,0.054491
ce_candidate_ci_family_review_k5_i4_recall_violation = 0.358277,0.047554
ce_candidate_ci_family_review_violation_regression_cells = 5
ce_candidate_ci_family_review_double_regression_cells = 1
normalization_invariant_improvement = false
route_aware_source_wide_generalization = false
next_todo = h002_route_aware_full_draft_plan_after_section_sync
ultimate_goal = route_aware_reliable_3d_relation_framework
current_main_success_route = comparison_compatibility
current_main_success_relations = relative_vertical,size_relative
ablation_review_result = S2_beats_A1_A2_aggregate_primary_route_violation_stable_recall_mixed
```

Primary validation table:

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
main_table = main_validation_table.csv
caption_ready_table = main_validation_table.md
source_family_caveats = source_family_caveats.csv
controls = control_table_compact.csv
```

Latest review gate:

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization/
status = h002_main_validation_table_review_after_materialization_ready
report = report/report_0703.md
```

Latest insertion plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review/
status = h002_paper_draft_insertion_plan_after_main_validation_table_review_ready
manuscript_files_edited = false
```

Latest `p_obs/p_rel` protocol:

```text
artifact_root = artifacts/compatibility_dataset_v3_pobs_prel_main_claim_protocol_after_report_0703/
status = h002_pobs_prel_main_claim_protocol_after_report_0703_ready
selected_path = include_pobs_prel_as_main_framework_claim_not_yet_quantitative_result
```

Latest `p_obs/p_rel` result review:

```text
artifact_root = artifacts/compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner/
status = h002_pobs_prel_result_review_after_metric_runner_ready
selective_metric_pass = true
paper_promotion_pass = false
```

Latest `p_obs/p_rel` CI/qualitative/failure review:

```text
artifact_root = artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review/
status = h002_ci_qualitative_failure_wording_after_pobs_prel_review_ready
selected_path = keep_pobs_prel_as_framework_component_ci_qualitative_wording_ready
paper_promotion_pass = false
```

Latest `p_obs/p_rel` calibration-upgrade review:

```text
runtime_root = experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/
artifact_root = artifacts/compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/
status = h002_pobs_prel_calibration_upgrade_result_review_after_runner_ready
validation_errors = 0
calibrated_quantitative_claim_pass = false
pobs_prel_framework_component_allowed = true
```

Latest `p_obs/p_rel` observability label fill / schema audit:

```text
label_runtime_root = experiments/H002_compatibility_routing/pobs_prel_observability_labels/latest/
ingestion_runtime_root = experiments/H002_compatibility_routing/pobs_prel_observability_ingestion/latest/
schema_audit_runtime_root = experiments/H002_compatibility_routing/pobs_prel_observability_schema_audit/latest/
status = h002_pobs_prel_observability_schema_audit_ready
validation_errors = 0
rows = 265
observable_clear = 135
ambiguous_evidence = 126
unobservable_missing_evidence = 4
blocked_field_hits = 0
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_metric_gate_decision
```

Latest `p_obs/p_rel` user-confirmed observability metric rerun:

```text
metric_gate_runtime_root = experiments/H002_compatibility_routing/pobs_prel_observability_metric_gate/latest/
metric_runtime_root = experiments/H002_compatibility_routing/pobs_prel_observability_metric/latest/
status = h002_pobs_prel_observability_metric_ready
validation_errors = 0
user_review_completed = true
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

Latest `p_obs/p_rel` observability metric result review:

```text
review_runtime_root = experiments/H002_compatibility_routing/pobs_prel_observability_metric_review/latest/
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

Latest `p_obs/p_rel` Q_e repair plan:

```text
runtime_root = experiments/H002_compatibility_routing/pobs_prel_qe_repair_plan/latest/
status = h002_pobs_prel_qe_repair_plan_ready
validation_errors = 0
failure_cause = qe_feature_label_mismatch
qe_repair_blocks = Q_e_asset_availability,Q_e_visual_coverage,Q_e_geometry_quality,Q_e_ambiguity,Q_e_state_v2
pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_materialization
```

Latest `p_obs/p_rel` Q_e repair materialization:

```text
runtime_root = experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest/
status = h002_pobs_prel_qe_repair_materialization_ready
validation_errors = 0
blocked_field_hits = 0
train_qe_v2_rows = 14604
eval_qe_v2_rows = 265
train_label_counts = observable_clear:4868,ambiguous_evidence:4868,unobservable_missing_evidence:4868
eval_alignment = observable_clear->sufficient:135,ambiguous_evidence->ambiguous:126,unobservable_missing_evidence->missing:4
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_schema_audit
```

Latest `p_obs/p_rel` Q_e repair schema audit:

```text
runtime_root = experiments/H002_compatibility_routing/pobs_prel_qe_repair_schema_audit/latest/
status = h002_pobs_prel_qe_repair_schema_audit_ready
validation_errors = 0
blocked_field_hits = 0
schema_separation = true
row_alignment = true
qe_required_blocks = true
train_label_balance = true
eval_ambiguous_missing_not_sufficient = true
pobs_only_diagnostic_metric_allowed = true
full_selective_decision_rerun_allowed = false
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_pobs_only_metric
```

Latest `p_obs/p_rel` Q_e repair p_obs-only metric:

```text
runtime_root = experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_only_metric/latest/
status = h002_pobs_prel_qe_repair_pobs_only_metric_ready
validation_errors = 0
train_rows = 14604
eval_rows = 265
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
abstain_precision = 1.000000
abstain_recall = 1.000000
observable_false_abstain_rate = 0.000000
legacy_all_sufficient_AUROC = 0.500000
legacy_all_sufficient_abstain_recall = 0.000000
diagnostic_pass = true
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_pobs_metric_review
```

Latest `p_obs/p_rel` Q_e repair p_obs metric review:

```text
runtime_root = experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_metric_review/latest/
status = h002_pobs_prel_qe_repair_pobs_metric_review_ready
validation_errors = 0
proxy_shortcut_risk = high
pobs_required_for_core_claim = false
pobs_main_claim_allowed = false
pobs_optional_framework_component = true
full_selective_decision_rerun_now = false
selected_path = demote_pobs_to_optional_diagnostic_keep_core_claim_on_Ce_source_reranking
next_todo = superseded_by_h002_ce_improvement_path
```

Latest H002 paper-outline / integration decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan/
status = h002_paper_outline_or_integration_decision_after_insertion_plan_ready
selected_path = open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root
h001_manuscript_edit_now = false
new_top_level_paper_folder_now = false
```

Latest H002 standalone-outline gap review:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision/
status = h002_standalone_outline_gap_review_after_decision_ready
selected_path = keep_outline_candidate_do_not_promote_paper_workspace_yet_resolve_gap_pack
promote_to_new_paper_workspace_now = false_at_that_stage
```

Latest H002 standalone gap-resolution pack:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/
status = h002_gap_resolution_pack_after_outline_review_ready
validation_errors = 0
resolved = claim_thesis,main_result_ci,table_ablation_contract,figure_specs,related_work_novelty_map,failure_taxonomy
workspace_promotion_allowed_now = false_at_that_stage
```

Latest H002 paper-workspace promotion decision:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack/
status = h002_paper_workspace_promotion_decision_after_gap_resolution_pack_ready
selected_path = promote_h002_to_dedicated_paper_workspace_no_h001_manuscript_edit_validation_main_claim
paper_workspace = paper/h002_compatibility_routing/
h001_manuscript_edit_now = false
new_top_level_paper_folder_created = false
```

Latest H002 paper-workspace route-aware sync:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync/
status = h002_paper_workspace_initial_draft_and_figure_table_sync_ready
goal = relation_aware_reliable_3d_relation_framework
current_main_success_route = comparison_compatibility
current_main_success_relations = relative_vertical,size_relative
next_todo = h002_source_reranking_ablation_expansion_plan_after_route_goal_update
```

Latest H002 source-reranking ablation expansion plan:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/
status = h002_source_reranking_ablation_expansion_plan_after_route_goal_update_ready
required_new_score_ids = A1_source_x_G_only,A2_source_x_TG_concat
required_table_fix = absolute_control_and_ablation_metrics
required_ci_fix = familywise_ci_for_ablation_deltas
next_todo = h002_source_reranking_ablation_expansion_implementation_after_plan
```

Latest H002 source-reranking ablation expansion implementation:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/
status = h002_source_reranking_ablation_expansion_implementation_after_plan_ready
implemented_score_ids = A1_source_x_G_only,A2_source_x_TG_concat
runtime_metric_root = experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
runtime_ci_root = experiments/H002_compatibility_routing/source_reranking_ci/latest/
primary_ablation_ci_pass = true
validation_errors = 0
next_todo = h002_source_reranking_ablation_expansion_result_review_after_implementation
```

Latest H002 source-reranking ablation result review:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/
status = h002_source_reranking_ablation_expansion_result_review_after_implementation_ready
result_interpretation = S2_beats_A1_A2_on_aggregate_primary_comparison_route
familywise_caveat = violation_stable_recall_mixed
table_placement = compact_main_candidate_full_appendix_required
claim_boundary = validation_level_comparison_route_scoped
paper_promotion_hold = true
validation_errors = 0
next_todo = h002_experiment_stage_remaining_gap_review_after_ablation_result_review
```

Latest H002 experiment-stage remaining-gap review:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_experiment_stage_remaining_gap_review_after_ablation_result_review/
status = h002_experiment_stage_remaining_gap_review_after_ablation_result_review_ready
best_current_claim = validation-level source reranking for geometry-checkable comparison relations using factor-isolated predicate-geometry compatibility
blocked_broad_claim = completed route-aware reliable 3D relation framework across all 3DSSG relation families
paper_claim_strength = moderate_to_good_if_scoped
standalone_top_tier_risk = high_unless_claim_is_scoped_and_defended
remaining_sensitivity = normalization uses label-free validation candidate-pool bounds; G-only ablation is route-aware because G_e includes route_family one-hot
validation_errors = 0
next_todo = h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review
```

Latest H002 normalization/no-route geometry sensitivity review:

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/
artifact_root = artifacts/compatibility_dataset_v3_h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review/
status = h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review_ready
validation_errors = 0
method_principle = natural_and_principled_for_scoped_problem
relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
general_reliable_3d_relation_framework = not_yet_validated
normalization_decision = minmax_main_allowed_with_raw_product_sensitivity_and_rankpct_caveat
geometry_only_decision = no_route_g_only_sensitivity_passed; S2 gain is not explained by route-family one-hot geometry baseline
paper_claim_decision = comparison_route_main_claim_allowed; broad_general_framework_claim_blocked
next_todo = h002_paper_claim_boundary_update_after_sensitivity_review
```

Latest H002 paper claim boundary update after sensitivity review:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_paper_claim_boundary_update_after_sensitivity_review/
status = h002_paper_claim_boundary_update_after_sensitivity_review_ready
validation_errors = 0
locked_claim = validation_level_comparison_route_source_reranking
comparison_route_main_claim_allowed = true
relation_aware_framework_partially_validated = true
general_reliable_framework_completed_result = false
pobs_prel_solved_claim_allowed = false
normalization_invariant_claim_allowed = false
next_todo = support_contact_generalization_repair
```

Latest H002 general-framework gap synthesis:

```text
runtime_root = experiments/H002_compatibility_routing/general_framework_gap/latest/
status = h002_general_framework_gap_experiment_synthesis_ready
validation_errors = 0
general_framework_claim = blocked_continue_experiment_stage
support_contact_solved = false
calibrated_pobs_prel_solved = false
normalization_invariant_improvement = false
route_aware_source_wide_generalization = false
next_todo = support_contact_generalization_repair
```

Latest H002 C_e improvement path:

```text
runtime_root = experiments/H002_compatibility_routing/ce_improvement_path/latest/
report = hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0706.md
status = h002_ce_improvement_path_ready
validation_errors = 0
source_rows_scored = 762888
best_primary_score = I4_calibrated_route_aware_source_x_Ce
calibrated_ce_candidate_pass = true
calibrated_ce_main_promotion = false
richer_ge_support_contact_promotion = false
pobs_prel_reopened = false
next_todo = h002_ce_candidate_ci_family_review_before_promotion
```

Latest H002 C_e candidate CI/family review:

```text
runtime_root = experiments/H002_compatibility_routing/ce_candidate_ci_family_review/latest/
report = hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0706.md
status = h002_ce_candidate_ci_family_review_ready
validation_errors = 0
n_bootstrap = 1000
candidate_score = I4_calibrated_route_aware_source_x_Ce
baseline_score = S2_current_source_x_Ce
K5_S2_recall_violation = 0.352608,0.054491
K5_I4_recall_violation = 0.358277,0.047554
violation_regression_cells = 5
double_regression_cells = 1
promote_to_main_score = false
selected_path = keep_current_main_score_report_I4_as_candidate_or_ablation
next_todo = h002_route_aware_full_draft_plan_after_section_sync
```

Latest framework-direction decision:

```text
selected_paper_direction = relation_aware_evidence_routing
framework_claim = route_specific_evidence_is_required_for_reliable_3d_relations
validated_mechanism = predicate_geometry_compatibility_route
validated_quantitative_scope = relative_vertical,size_relative
main_score = S2_current_source_x_Ce
i4_role = secondary_candidate_ablation
blocked_wording = completed_general_reliable_3d_relation_framework,all_relation_types_solved,support_contact_solved,calibrated_pobs_prel_solved
status = h002_relation_aware_framework_claim_hierarchy_and_route_protocol_ready
section_sync_status = h002_route_aware_paper_section_sync_after_protocol_freeze_ready
next_todo = h002_route_aware_full_draft_plan_after_section_sync
```

Latest path map:

| Path | Role |
| --- | --- |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0703.md` | score extraction and table-review explanation |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0704.md` | full claim, novelty-threat, score-process, and principle review |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0705.md` | principle, sensitivity, relation-aware framework scope, and claim-boundary lock |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/report/report_0706.md` | hard-negative, route-aware, richer-G_e, and calibrated C_e improvement-path result |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/` | caption-ready table material |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization/` | review checks and wording gate |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review/` | insertion plan, caption/footnote, snippets, blocked wording |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_pobs_prel_main_claim_protocol_after_report_0703/` | `Q_e`, target, selective metric, missing-evidence control, and failure-route protocol |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner/` | p_obs/p_rel selective metric result review |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review/` | p_obs/p_rel CI, qualitative examples, and failure wording |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/` | p_obs/p_rel calibration-upgrade review and six-check decision |
| `experiments/H002_compatibility_routing/pobs_prel_observability_labels/latest/` | Codex-filled p_obs/p_rel observability labels |
| `experiments/H002_compatibility_routing/pobs_prel_observability_ingestion/latest/` | model-safe Q_e / p_rel views and hidden observability labels |
| `experiments/H002_compatibility_routing/pobs_prel_observability_schema_audit/latest/` | schema separation audit for the observability label views |
| `experiments/H002_compatibility_routing/pobs_prel_observability_metric_gate/latest/` | user-confirmation gate allowing diagnostic metric rerun |
| `experiments/H002_compatibility_routing/pobs_prel_observability_metric/latest/` | diagnostic p_obs/p_rel metric rerun on the user-confirmed observability subset |
| `experiments/H002_compatibility_routing/pobs_prel_observability_metric_review/latest/` | p_obs failure / p_rel signal review and Q_e repair plan |
| `experiments/H002_compatibility_routing/pobs_prel_qe_repair_plan/latest/` | Q_e v2 schema, materialization contract, evaluation gates, and paper boundary |
| `experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest/` | repaired Q_e v2 train/eval views and hidden observability v2 labels |
| `experiments/H002_compatibility_routing/pobs_prel_qe_repair_schema_audit/latest/` | repaired Q_e v2 schema, leakage, row-alignment, and state-alignment audit |
| `experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_only_metric/latest/` | repaired Q_e v2 p_obs-only diagnostic smoke test |
| `experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_metric_review/latest/` | p_obs-only result review and optionalization decision |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan/` | standalone outline decision, paper outline, integration boundary |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision/` | gap matrix, table/figure plan, promotion gates |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/` | claim thesis, bootstrap CI, final table/ablation contract, figure specs, related-work map, support/contact failure taxonomy |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack/` | H002 paper-workspace promotion decision and claim boundary |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync/` | route-aware goal update, route readiness, and next ablation pointer |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_plan_after_route_goal_update/` | expanded source-reranking ablation/table/CI contract |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/` | implemented ablation output review gate and key metrics |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/` | A1/A2 interpretation, family-wise caveats, table placement, and claim wording |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_experiment_stage_remaining_gap_review_after_ablation_result_review/` | global claim/artifact/score/novelty/principle review and next sensitivity plan |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review/` | sensitivity key table, principle review, framework scope review, and paper-boundary decision |
| `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_paper_claim_boundary_update_after_sensitivity_review/` | paper claim boundary lock after sensitivity review |
| `paper/h002_compatibility_routing/` | promoted standalone H002 paper workspace |
| `paper/h002_compatibility_routing/route_framework.md` | relation-family route map and framework expansion plan |
| `experiments/H002_compatibility_routing/source_reranking_materialization/latest/` | source-wide model-safe input views |
| `experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/` | schema/leakage audit outputs |
| `experiments/H002_compatibility_routing/source_reranking_evaluation/latest/` | score and metric outputs |
| `experiments/H002_compatibility_routing/source_reranking_ci/latest/` | source-reranking bootstrap CI outputs |
| `experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/` | normalization and no-route G-only sensitivity outputs |
| `experiments/H002_compatibility_routing/ce_improvement_path/latest/` | hard-negative/structured, route-aware, richer-G_e gate, and calibrated C_e outputs |
| `experiments/H002_compatibility_routing/ce_candidate_ci_family_review/latest/` | bootstrap CI, family-wise blocker, K=5 result, and main-score promotion decision for I4 |
| `experiments/H002_compatibility_routing/pobs_prel_materialization/latest/` | p_obs/p_rel materialized `Q_e`, `p_rel`, hidden-label views |
| `experiments/H002_compatibility_routing/pobs_prel_schema_audit/latest/` | p_obs/p_rel schema separation audit |
| `experiments/H002_compatibility_routing/pobs_prel_evaluation/latest/` | p_obs/p_rel selective metrics and gate decision |
| `experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/` | p_obs/p_rel calibration split, asset audit, controls, CI, and failure-route connection |
| `experiments/H002_compatibility_routing/scripts/` | executable runtime code |

Boundary:

- split: official 3DSSG validation split
- sources: VL-SAT and Open3DSG validation predictions
- metrics: Recall@K and custom Violation@K
- primary families: relative_vertical + size_relative
- official test / SOTA / leaderboard / unconstrained open-set GT claims: blocked
- Open3DSG wording: open-vocabulary source, closed-vocabulary 3DSSG mapping for quantitative evaluation
- `p_obs/p_rel`: included as main framework selective decision layer; selective
  stress-test metrics passed, but calibrated quantitative paper-result wording
  remains blocked after the calibration-upgrade run because `p_rel` ECE worsened,
  asset-audit labels had no negative/ambiguous rows, and attachment/containment
  rows are absent
- H002 paper position: promoted to standalone paper workspace under
  `paper/h002_compatibility_routing/`; not H001 manuscript integration
- H002 goal: route-aware reliable 3D relation framework; current main
  quantitative success is comparison compatibility (`relative_vertical`,
  `size_relative`)
- H002 paper workspace promotion: complete as a `paper/` subfolder; no new
  top-level paper folder was created
- H003 embedding: future/optional extension, not current main claim

## Core Runtime Code

These scripts under `experiments/H002_compatibility_routing/scripts/` are the
actual executable code path for paper-level evidence:

| Code | Role |
| --- | --- |
| `materialize_source_reranking_candidates.py` | builds source-wide model-safe views, source-score view, and hidden metric manifest |
| `audit_source_reranking_materialization_schema.py` | checks leakage/schema separation before scoring |
| `run_source_reranking_metric.py` | fits frozen C_e plus `A1` geometry-only and `A2` concat ablations on internal train rows, then evaluates source reranking on validation source rows |
| `bootstrap_source_reranking_ci.py` | bootstraps source-reranking Recall@K / Violation@K, `S2-S0`, `S2-A1`, `S2-A2`, control deltas, and family-wise CI |
| `run_ce_improvement_path.py` | evaluates hard-negative/structured, route-aware, richer-G_e gate, and calibrated C_e variants |
| `run_official_metric.py` | route/family mechanism evaluation for C_e before source reranking |
| `official_materialize_candidates.py` | materializes official-validation candidate rows for route-family evaluation |
| `audit_official_materialization_schema.py` | checks model-safe / hidden-field separation for official candidate rows |
| `materialize_support_contact_harder_route.py` | diagnostic hard-route materialization for support/contact failure taxonomy |
| `run_support_contact_harder_metric.py` | diagnostic support/contact hard-route evaluation; not a success claim |
| `materialize_pobs_prel_selective.py` | materializes `Q_e`, `p_rel`, and hidden selective labels |
| `audit_pobs_prel_materialization_schema.py` | audits p_obs/p_rel model-safe and hidden-field separation |
| `run_pobs_prel_selective_metric.py` | evaluates p_obs, p_rel, accept/reject/abstain, calibration, and risk-coverage |
| `run_pobs_prel_calibration_upgrade.py` | evaluates fixed-split calibration, asset-observability audit, missing/wrong-pair controls, CI, and failure-route connection |
| `materialize_pobs_prel_qe_repair.py` | materializes repaired Q_e v2 train/eval views |
| `audit_pobs_prel_qe_repair_schema.py` | audits repaired Q_e v2 schema separation and p_obs-only rerun readiness |
| `run_pobs_prel_qe_repair_pobs_only_metric.py` | runs repaired Q_e v2 p_obs-only diagnostic metric |
| `review_pobs_prel_qe_repair_pobs_metric.py` | reviews p_obs-only diagnostic pass and demotes p_obs from the core claim |

## Score Outputs

Runtime score outputs live under:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

Key files:

| File | Meaning |
| --- | --- |
| `score_manifest.json` | score construction, C_e/source-score bounds, provenance |
| `score_condition_metrics.csv` | aggregate metric by score condition |
| `source_family_metrics.csv` | source/family/K metric table |
| `control_metrics.csv` | S2 vs S0, C_e-only, shuffled-C_e, wrong-T controls |
| `selected_predictions.jsonl` | selected top-K prediction rows |

Source-wide materialized input views live under:

```text
experiments/H002_compatibility_routing/source_reranking_materialization/latest/
```

Key files:

| File | Meaning |
| --- | --- |
| `model_safe_ce_view.jsonl` | T_e and G_e only; input for C_e |
| `model_safe_geometry_only_view.jsonl` | geometry-only diagnostic view |
| `source_rank_view.jsonl` | Z_e source score/rank; final reranking only |
| `hidden_metric_manifest.jsonl` | GT/violation labels; metric-only, never model input |

## Core Hypothesis Tools Kept In This Folder

`tools/` now keeps only paper-claim chain validators and table materializers.
Most historical target-mining, smoke, and path-search scripts are archived.

Important kept tools:

- `compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review.py`
- `compatibility_dataset_v3_main_validation_table_review_after_materialization.py`
- `compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock.py`
- `compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision.py`
- `compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze.py`
- `compatibility_dataset_v3_source_reranking_metric_result_review_after_runner.py`
- `compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization.py`
- `compatibility_dataset_v3_official_metric_runner_after_protocol_freeze.py`
- `compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze.py`

Archived files are preserved under:

```text
archive/hypothesis_records/hypothesis/H002_factorized-relation-confidence_cleanup_20260703/
```
