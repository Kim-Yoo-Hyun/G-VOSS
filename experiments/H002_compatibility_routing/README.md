# H002 Compatibility Routing Experiment

This is the Docker promotion skeleton for H002:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## Current Status

```text
status = main_validation_claim_table_locked_test_blocked
paper_level_ready = false
docker_preflight_run = true
route_materialization_run = true
materialization_schema_audit_run = true
grouped_split_protocol_run = true
grouped_eval_protocol_run = true
grouped_eval_runner_run = true
grouped_holdout_run = true_internal_candidate_pool_only
official_validation_eval_only_usage = true
official_test_used = false
claim_boundary_review_run = true
official_validation_test_protocol_plan_run = true
official_validation_inventory_counted = true
official_source_inventory_run = true
official_candidate_materialization_protocol_run = true
official_candidate_materialization_docker_run = true
official_candidate_rows_materialized = true
official_candidate_materialization_schema_audit_run = true
official_candidate_materialization_schema_audit_ready = true_with_support_contact_shortcut_caveat
official_metric_protocol_freeze_run = true
official_metric_protocol_freeze_ready = true
official_metric_runner_run = true
official_validation_metric_produced = true
official_metric_runner_ready = true_with_caveats
official_metric_result_review_run = true
paper_level_experiment_execution_gate = passed_with_caveats
official_metric_claim_boundary_lock_run = true
paper_table_draft_allowed = true
paper_table_skeleton_run = true
paper_table_skeleton_ready = true
paper_table_skeleton_review_run = true
principled_structure = true
bounded_mechanism_evidence_only = true
principled_design_gap_plan_run = true
selected_gap = harder_support_contact_route
support_contact_harder_route_protocol_run = true
support_contact_harder_route_source_inventory_run = true
support_contact_harder_route_materialization_plan_run = true
support_contact_harder_route_docker_materialization_run = true
support_contact_harder_route_schema_shortcut_audit_run = true
support_contact_harder_route_schema_shortcut_audit_ready = true_with_shortcut_warnings
support_contact_harder_route_metric_protocol_freeze_run = true
support_contact_harder_route_metric_protocol_ready = true
support_contact_harder_route_train_eval_alignment_run = true
support_contact_harder_route_train_eval_feature_parity = ready_with_derived_proxy_mappings
support_contact_harder_route_metric_runner_run = true
support_contact_harder_route_metric_runner_validation_errors = 0
support_contact_harder_route_official_validation_m4_auroc = 0.077539
support_contact_harder_route_wrong_t_auroc = 0.922461
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
source_reranking_metric_protocol_freeze_run = true
source_reranking_metric_protocol_freeze_ready = true
source_reranking_metric_protocol_validation_errors = 0
source_reranking_primary_score = S2_source_x_Ce
source_reranking_metric_runner_run = true
source_reranking_metric_runner_ready = true
source_reranking_metric_runner_validation_errors = 0
source_reranking_source_rows_scored = 762888
source_reranking_internal_train_rows = 4868
source_reranking_selected_prediction_rows = 932732
source_reranking_metric_result_review_ready = true
source_reranking_validation_evidence = positive
source_reranking_negative_recall_cells = 3
source_reranking_violation_nonimprove_cells = 0
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
source_deployable_experiment = blocked_keep_validation_appendix_external_provenance_next
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
official_test_benchmark_claim_allowed = false
open3dsg_source_boundary = open_vocabulary_source_closed_vocabulary_3dssg_mapping
h003_embedding_extension_in_main_claim_now = false
h003_embedding_extension_future_optional = true
checkpoint_reproduction_is_sufficient_for_test_recall = false
prediction_only_test_scan_export_is_sufficient_for_test_recall = false
p_obs_p_rel_branch = defer_until_independent_observability_labels
final_paper_result_promotion = not_yet
h001_source_inventory_read_only = true
next_todo = compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock
```

## Role

This folder will own H002 Docker experiment records once the branch is promoted beyond hypothesis-stage artifacts.

It does not replace the hypothesis record under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/
```

The hypothesis folder remains the owner of method framing, route-specific probe history, and train-only smoke artifacts.
This experiment folder owns future Docker commands, run manifests, grouped-holdout outputs, shortcut audits, and promotion decisions.

## Current Boundary

No final official-test H002 paper metric has been produced from this folder.
Validation-level H002 mechanism and source-reranking metrics exist, but remain
bounded by their claim-lock artifacts.

Docker preflight has passed and wrote:

```text
experiments/H002_compatibility_routing/preflight/latest/mount_check.json
experiments/H002_compatibility_routing/preflight/latest/run_manifest.json
experiments/H002_compatibility_routing/preflight/latest/validation_errors.jsonl
```

Route materialization has also passed and wrote:

```text
experiments/H002_compatibility_routing/materialization/latest/route_rows.jsonl
experiments/H002_compatibility_routing/materialization/latest/model_safe_view.jsonl
experiments/H002_compatibility_routing/materialization/latest/hidden_manifest.jsonl
experiments/H002_compatibility_routing/materialization/latest/row_manifest.json
experiments/H002_compatibility_routing/materialization/latest/validation_errors.jsonl
```

Materialized route rows total `6952` rows across `relative_vertical`, `size_relative`, `relative_horizontal`, and `support_contact`.

Materialization schema audit has passed and wrote:

```text
experiments/H002_compatibility_routing/schema_audit/latest/audit_manifest.json
experiments/H002_compatibility_routing/schema_audit/latest/schema_violations.jsonl
experiments/H002_compatibility_routing/schema_audit/latest/blocked_field_hits.jsonl
experiments/H002_compatibility_routing/schema_audit/latest/high_shortcut_warnings.jsonl
experiments/H002_compatibility_routing/schema_audit/latest/shortcut_risk_table.csv
experiments/H002_compatibility_routing/schema_audit/latest/split_readiness_table.csv
```

Schema errors, blocked `C_e` field hits, and high-risk `C_e` allowed shortcut warnings are all `0`. All four promoted route families are split-ready.

Grouped split protocol has passed and wrote:

```text
experiments/H002_compatibility_routing/splits/latest/model_safe_split_view.jsonl
experiments/H002_compatibility_routing/splits/latest/split_assignments.jsonl
experiments/H002_compatibility_routing/splits/latest/group_manifest.jsonl
experiments/H002_compatibility_routing/splits/latest/split_manifest.json
experiments/H002_compatibility_routing/splits/latest/route_split_counts.csv
experiments/H002_compatibility_routing/splits/latest/predicate_split_counts.csv
experiments/H002_compatibility_routing/splits/latest/leakage_audit.csv
experiments/H002_compatibility_routing/splits/latest/validation_errors.jsonl
```

The split covers `6952` rows and `3684` `cv_group_id` groups with `0` validation errors. All `cv_group_id` groups are assigned to exactly one of `internal_train`, `internal_dev`, or `internal_heldout`.

Grouped evaluation protocol has also passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/
```

It fixes the `C_e` metric contract before any grouped metric run. Main `C_e` evaluation may use only `T_e` and `G_e`; `Z_e` and `Q_e` remain diagnostic-only until a later `p_rel` / `p_obs` protocol.

The grouped holdout planned for H002 is inside the H002 candidate source pool. It must not be described as official validation/test unless a later protocol explicitly adopts official splits.

Grouped evaluation runner has now passed and wrote:

```text
experiments/H002_compatibility_routing/evaluation/latest/eval_manifest.json
experiments/H002_compatibility_routing/evaluation/latest/model_view_manifest.json
experiments/H002_compatibility_routing/evaluation/latest/route_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/predicate_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/control_metrics.csv
experiments/H002_compatibility_routing/evaluation/latest/prediction_scores.jsonl
experiments/H002_compatibility_routing/evaluation/latest/leakage_audit.csv
experiments/H002_compatibility_routing/evaluation/latest/validation_errors.jsonl
```

After feature extractor repair, the internal heldout aggregate supports a nontrivial `T_e x G_e` compatibility signal: `M4_TxG_compatibility` heldout AUROC is `0.984976`, compared with `M1_T_semantic_only` `0.454321`, `M2_G_geometry_only` `0.487690`, `M3_T_plus_G_concat` `0.465868`, wrong-`T_e` control `0.014425`, and shuffled-`G_e` control `0.493975`.

Family-level behavior after repair: `size_relative`, `relative_vertical`, and `relative_horizontal` are claim-supporting; `support_contact` remains partial/challenging.

Grouped evaluation result review has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/
```

Relative-vertical failure analysis has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/
```

The analysis found an implementation-level feature extraction issue: the runner selected `raw_geometry_feature_available_mask.center_delta_z` instead of `raw_geometry_feature_vector.center_delta_z`.

Grouped-eval feature extractor repair has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis/
```

The next step is repaired grouped-eval claim-boundary review.

Repaired grouped-eval claim-boundary review has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/
```

The boundary locks `relative_horizontal`, `relative_vertical`, and
`size_relative` as main internal `C_e` compatibility evidence, keeps
`support_contact` as partial/challenging, and blocks official validation/test,
calibrated `p_rel/p_obs`, solved support/contact, all-relation generalization,
and aggregate-only claims.

The official validation/test protocol plan has since completed. Do not promote
the current internal candidate-pool grouped metrics to paper results.

Official validation/test protocol plan has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/
```

The plan counted local `3DSSG_subset` split capacity only. It did not produce
official validation metrics. Local validation has 548 scans / 11,254 relations;
no local `relationships_test.json` was observed. Official source inventory has
since completed for validation GT, object/geometry joins, and optional
VL-SAT/Open3DSG source candidates.

Official source inventory has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
```

The inventory found official validation GT/object geometry candidate material for
`relative_horizontal 5474`, `relative_vertical 390`, `size_relative 170`, and
`support_contact 1589`, all with OBB pair coverage `1.0`. VL-SAT and Open3DSG
recovery source candidates are available as read-only H001 references. H001
geometry verification is checkable for `relative_vertical` and `support_contact`
but unsupported for `relative_horizontal` and `size_relative`; those routes need
H002-specific `G_e` materialization. No official metric or paper-level result was
produced. Official candidate materialization protocol has since completed.

Official candidate materialization protocol has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
```

The protocol freezes official validation GT/counterfactual materialization,
family-specific `G_e`, source-bridge handling, blocked fields, and required
audits. The implementation step belongs in this experiment root as Docker
service `h002-official-materialize-candidates`. It wrote:

```text
experiments/H002_compatibility_routing/official_materialization/latest/candidate_rows.jsonl
experiments/H002_compatibility_routing/official_materialization/latest/model_safe_view.jsonl
experiments/H002_compatibility_routing/official_materialization/latest/hidden_manifest.jsonl
experiments/H002_compatibility_routing/official_materialization/latest/row_manifest.json
experiments/H002_compatibility_routing/official_materialization/latest/validation_errors.jsonl
```

This runner has completed and is still not a metric runner.

Support/contact hard-route source inventory has also passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol/
```

It found that the current official validation support/contact materialization has
`3178` rows over `156` scans with balanced `standing on` / `lying on` labels, but
only OBB-proxy `G_e` is currently materialized. The underlying validation source
assets contain semseg, aligned PLY, mesh, segment, sequence, OBB, and dominant
normal fields for all support/contact rows, so a richer hard-route materializer is
feasible. `predicate_x_class_pair` shortcut risk remains high, so the next step is
materialization planning and audit design, not paper-result promotion.

Support/contact hard-route materialization plan has now passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory/
```

It freezes the next Docker materializer contract: official validation
support/contact remains eval-only, official test is unused, the output root is
planned as `experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/`,
and the primary model-safe view is `model_safe_main_no_class`. The next work is a
Docker materializer implementation, not a metric run.

Support/contact hard-route Docker materialization has completed under:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```

It wrote `3178` candidate/model-safe/hidden rows, `1589` group rows, `43` richer
`G_e` features, and `0` runtime validation errors. The stage review artifact is:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan/
```

This is still not a metric run. The next step is schema/shortcut audit.

Observed official materialization:

```text
candidate_rows = 23062
model_safe_view = 23062
hidden_manifest = 23062
validation_errors = 0
official_validation_metric = false
paper_metric = false
```

Family label counts:

| Family | Label 0 | Label 1 | Total |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 13290 | 5474 | 18764 |
| `relative_vertical` | 390 | 390 | 780 |
| `size_relative` | 170 | 170 | 340 |
| `support_contact` | 1589 | 1589 | 3178 |

Official materialization schema/shortcut audit has also passed with caveats and
wrote:

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

Observed official schema audit:

```text
schema_violations = 0
blocked_field_hits = 0
runtime_validation_errors = 0
model_safe_rows = 23062
hidden_rows = 23062
model_safe_hidden_mismatch = 0
control_readiness_blockers = 0
shortcut_warnings = 1
```

The caveat is `support_contact` `predicate_x_class_pair` majority accuracy
`0.993707`. This does not block the official metric-freeze step, but it blocks
any solved/main `support_contact` claim. `support_contact` remains a
challenging/diagnostic route unless later controlled repair changes the evidence.

The schema-audit result required official metric protocol freeze before any
metric run, so family-wise/macro/weighted reporting, control metrics, `Z_e`
exclusion from main `C_e`, and support-contact wording were fixed next.

Official metric protocol freeze has passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
```

The protocol locks official validation rows as eval-only, primary metric
`macro_family_AUROC`, weighted/overall metrics as secondary, main `C_e` inputs
as `T_e` and `G_e` only, and required wrong-`T` / shuffled-`G` / route controls.
It keeps `support_contact` challenging/diagnostic and does not compute a metric.

The next step is to add/run a Docker official metric runner that writes:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

The runner must not fit or tune on official validation and must not use official
test.

Official metric runner has completed once with exit 0 and wrote:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/eval_manifest.json
experiments/H002_compatibility_routing/official_evaluation/latest/model_view_manifest.json
experiments/H002_compatibility_routing/official_evaluation/latest/family_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/predicate_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/aggregate_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/control_metrics.csv
experiments/H002_compatibility_routing/official_evaluation/latest/prediction_scores.jsonl
experiments/H002_compatibility_routing/official_evaluation/latest/leakage_audit.csv
experiments/H002_compatibility_routing/official_evaluation/latest/validation_errors.jsonl
```

Observed official metric snapshot:

```text
M4_TxG_compatibility macro_family_AUROC = 0.8355465299908279
M4_TxG_compatibility weighted_family_AUROC = 0.7207808044279794
M4_TxG_compatibility overall_AUROC = 0.724835499373417
validation_errors = 0
official_test_usage = false
paper_metric_produced = false
```

Caveats: `support_contact` remains challenging with M4 AUROC `0.6317116456316851`;
`relative_horizontal` needs result review because horizontal frame-swap control
has weak macro delta `0.03814880004643195`. The next gate is official metric
result review and claim-boundary lock.

Official metric result review has now passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
```

The review marks the paper-level experiment execution gate as
`passed_with_caveats`, but does not promote a final paper result. `relative_vertical`
and `size_relative` are main paper-candidate evidence, `relative_horizontal` is
candidate evidence with a frame-control caveat, and `support_contact` remains
diagnostic/challenging only. The next gate is claim-boundary lock.

Official metric claim-boundary lock has now passed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review/
```

The lock allows a bounded paper-table draft. `relative_vertical` and
`size_relative` are primary mechanism rows, `relative_horizontal` is a caveated
frame-aware row, and `support_contact` is a diagnostic/failure-taxonomy row. Final
paper result promotion, official test claims, source reranking claims, calibrated
`p_rel`/`p_obs` claims, and all-relation/SOTA wording remain blocked.

Bounded paper-table skeleton now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock/
```

The skeleton uses `relative_vertical + size_relative` as the primary mechanism
macro, reports `relative_horizontal` as a caveated frame-aware row, and keeps
`support_contact` as a diagnostic/failure-taxonomy row. It is ready for table
review, not final paper-result promotion.

Paper table skeleton review now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock/
```

The review concludes that the H002 structure is principled and natural, but the
current primary evidence is too clean/signed-comparison-heavy for standalone
paper-result promotion. Keep the table as bounded mechanism evidence and plan a
harder-route or source-deployable evidence gap next.

Principled design gap plan now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review/
```

The selected next gap is `harder_support_contact_route`. The next protocol should
focus on `standing on` and `lying on`, keep `supported by` diagnostic, enrich
predicate-independent `G_e` with pose/contact/overlap/gap/point/mesh evidence,
and keep `Z_e`/`Q_e` out of the main `C_e` input. Source-deployable reranking and
`p_rel`/`p_obs` remain deferred.

Support/contact harder-route protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan/
```

The protocol locks `standing on` and `lying on` as the main hard-route predicates,
keeps `supported by` diagnostic, requires richer predicate-independent `G_e`
fields, excludes `Z_e` and `Q_e` from the main `C_e` input, and blocks official
test / paper metric promotion. The next experiment-side action is source
inventory for feature availability and class-pair balance before materialization.

H001 artifacts are read-only references if used. This folder must not modify H001 outputs.

## Support/Contact Harder Route Schema Shortcut Audit

The richer support/contact schema/shortcut audit has completed once with exit 0:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-schema-audit
```

Runtime output:

```text
experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest/
```

Summary:

- rows: `3178`
- groups: `1589`
- richer `G_e` features: `43`
- validation errors: `0`
- blocked field hits: `0`
- control readiness: `7/7`
- shortcut warnings: `3`
- high shortcut warnings: `2`

The audit allows metric protocol freeze but does not allow a solved
`support_contact` claim. The next step is protocol freeze for the hard-route
metric, not immediate source reranking or `p_obs`/`p_rel`.

## Support/Contact Harder Route Metric Protocol Freeze

The support/contact hard-route metric protocol has been frozen under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit/
```

Frozen metric:

- target: `C_e`
- primary metric: `support_contact_AUROC`
- primary model: `M4_TxG_compatibility`
- baselines: `M1_predicate_only`, `M2_geometry_only`, `M3_T_plus_G_concat`
- diagnostics: class-ablation, `Q_e`, `predicate x class-pair`
- controls: wrong-`T`, global shuffled-`G`, within-class-pair shuffled-`G`

Do not add or run the metric runner yet. The next experiment-side gate is
train/eval feature alignment because official validation has `43` canonical
hard-route `G_e` features while the available train reference has a different
prefixed `63`-feature schema.

## Support/Contact Harder Route Train/Eval Alignment

Train/eval feature alignment has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze/
```

Runner-ready inputs:

```text
model_safe_no_class_train_dev.jsonl
class_ablation_train_dev.jsonl
hidden_train_dev_manifest.jsonl
runner_input_contract.json
```

Summary:

- aligned rows: `640`
- internal train/dev rows: `531` / `109`
- official validation scan overlap: `0`
- official validation endpoint overlap: `0`
- official canonical features mapped: `43/43`
- derived/proxy mappings: `12/43`

The next stage may add a Docker metric runner, but it must fit only on
`internal_train`, select only on `internal_dev`, and evaluate official validation
once as eval-only.

## Support/Contact Harder Route Metric Runner

The support/contact hard-route metric runner has completed once with exit 0:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-metric-runner
```

Runtime output:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
```

Stage review artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment/
```

Summary:

- validation errors: `0`
- internal dev `M4_TxG_compatibility` AUROC: `0.721356`
- official validation `M4_TxG_compatibility` AUROC: `0.077539`
- official validation wrong-`T` AUROC: `0.922461`
- official validation rows: `3178`, eval-only
- official test usage: `false`

This is not promoted as a paper-facing support/contact success result. The next
stage is result review, focused on target construction mismatch, feature
distribution shift, and predicate sign convention.

Source-reranking materialization has completed under:

```text
experiments/H002_compatibility_routing/source_reranking_materialization/latest/
```

It wrote:

```text
source_candidates.jsonl = 762888
model_safe_ce_view.jsonl = 762888
model_safe_geometry_only_view.jsonl = 762888
source_rank_view.jsonl = 762888
hidden_metric_manifest.jsonl = 762888
validation_errors.jsonl = 0
```

The source split is `441696` VL-SAT rows and `321192` Open3DSG rows. The
primary success families, `relative_vertical` and `size_relative`, total
`254296` rows. No source reranking metric, official test, or paper result was
produced.

Source-reranking materialization schema audit has completed under:

```text
experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
```

Audit result:

```text
candidate_id_alignment = pass
model_safe_ce_view = T_e + G_e only
blocked_C_e_feature_hits = 0
source_rank_view = Z_e reranking-only
hidden_metric_manifest = metric-only
primary_success_families = balanced
support_contact = diagnostic excluded
validation_errors = 0
```

No source reranking metric, official test, or paper result was produced. The
next step is source-reranking metric protocol freeze.

Source-reranking metric protocol freeze has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit/
```

Frozen protocol summary:

```text
primary_score = S2_source_x_Ce
K_grid = 5,10,20,50,100
primary_success_families = relative_vertical,size_relative
support_contact = diagnostic excluded
validation_errors = 0
official_test_used = false
metric_runner_executed = false
```

The next experiment-side action is a Docker source-reranking metric runner that
computes `Recall@K`, `Violation@K`, and `Selected@K` for `S0`, `S1`, `S2`, and
the frozen controls. It must keep official validation eval-only and must not use
official test.

Source-reranking metric runner has completed under:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

Observed runtime summary:

```text
source_rows_scored = 762888
internal_train_rows_for_C_e = 4868
selected_prediction_rows = 932732
validation_errors = 0
official_test_usage = false
primary_score = S2_source_x_Ce
```

Primary weighted `S2_source_x_Ce` improves/preserves Recall@K and lowers
Violation@K versus `S0_source_score` for all frozen K. This is still
validation-level source-reranking evidence; the next stage is result review
before claim promotion.

Source-reranking metric result review has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner/
```

Review summary:

```text
source_reranking_validation_evidence = positive
weighted_S2_vs_S0_recall_nonnegative_all_K = true
weighted_S2_vs_S0_violation_nonpositive_all_K = true
source_family_cells = 20
negative_recall_cells = 3
violation_nonimprove_cells = 0
official_test_usage = false
paper_promotion = not_yet
```

Source-reranking claim-boundary lock has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review/
```

The result is locked as validation-level deployability evidence. It can be
drafted as a secondary validation table candidate or appendix table, but not as
official test, final paper, SOTA, uniform-improvement, or `C_e`-alone deployable
evidence. The next stage is a bounded validation table skeleton.

Source-reranking validation table skeleton has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock/
```

It writes 5 primary tradeoff rows, 15 control rows, 3 required caveat rows, and
the 20-row source-family table. The next stage is a table review deciding
main-text secondary evidence versus appendix-only placement.

Source-reranking validation table review has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton/
```

The validation table is now downgraded to appendix or secondary analysis. The
main benchmark table must use an independent test set or accepted official
evaluation server. Current test benchmark is not ready: canonical
`relationships_test.json` is missing, and observed staged test files overlap
validation scans until provenance and split-disjointness are verified.

Test benchmark preflight has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade/
```

The preflight is complete but blocked. It found no canonical test file, `2`
non-empty staged test candidates that overlap validation scans, and `0`
official-test source rows. Do not open an experiments-level test benchmark until
source resolution passes.

Test benchmark source resolution has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight/
```

The source-resolution gate is complete but blocked. It confirms that 3RScan has
a scan-level test split, but this is insufficient for H002 because the branch
needs independent 3DSSG relation-test labels and source predictions on the exact
test candidate pool. No accepted public relation evaluation server or usable
local `relationships_test.json` provenance is confirmed. Keep the validation
table as appendix/secondary evidence and do not run a test benchmark service.

External provenance request packet has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution/
```

This packet is ready, but it does not unblock test execution. It records that
VL-SAT/Open3DSG checkpoint or prediction routes are insufficient for test
`Recall@K` without relation-label GT or an accepted evaluation server. The next
step is response/provenance ingestion, not a Docker metric runner.

External response ingestion has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request/
```

No response or official provenance artifact was found. Do not open an H002 test
benchmark Docker service from this experiment root. Validation source-reranking
results remain appendix/secondary analysis until an official response or
documentation changes the provenance state.

Validation-only position lock has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response/
```

This locks H002 source-reranking as an official-3DSSG-validation custom
evaluation, not an official test benchmark. Open3DSG may be described as an
open-vocabulary source only with the caveat that quantitative evaluation is
closed-vocabulary 3DSSG label mapping. Keep test benchmark Docker services
closed unless the reopen conditions are met.

Post-validation path decision has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision/
```

This supersedes the appendix-only interpretation. H002 source-reranking can be
used as a main validation benchmark table because VL-SAT/Open3DSG are compared on
the same official 3DSSG validation GT. This still does not open official-test or
leaderboard/SOTA claims.

Main validation claim/table lock has completed under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision/
```

The next experiment-folder action is compact table materialization, not a new
metric run. H003 embedding remains future/optional unless a separate prototype
proves improvements over explicit `C_e`.

## Candidate Promotion Routes

| Family | Predicates | Role |
| --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | candidate clean compatibility route |
| `size_relative` | `bigger than`, `smaller than` | candidate clean compatibility route |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | candidate frame-aware route |
| `support_contact` | `standing on`, `lying on` | candidate challenging compatibility route |

Diagnostic/deferred routes such as `close by`, `supported by`, R7 attachment-like relations, containment, cover, leaning, identity/symmetry, and semantic/structural relations are not promoted in the current path.

## Required Gates

1. Docker preflight.
2. Route materialization inside Docker.
3. Schema, shortcut, and leakage audits.
4. Grouped split protocol over `cv_group_id`.
5. Grouped evaluation protocol.
6. Grouped evaluation runner.
7. Result review and family-level claim boundary.
8. Official validation/test protocol plan.
9. Official source inventory.
10. Official candidate materialization protocol.
11. Official candidate materialization Docker runner.
12. Official materialization schema/shortcut audit.
13. Official metric protocol freeze.
14. Official metric runner.
15. Official metric result review and claim-boundary lock.
16. Optional calibration/selective-decision evaluation for `p_rel` / `p_obs`.
17. Claim wording lock.

## Local Owners

- `README.md`: folder boundary, status, and gate summary.
- `commands.md`: future Docker command index and expected outputs.
- Docker configuration root: `configs/h002/`.
- Compact results root: `results/h002_compatibility_routing/`.
