# H002 Compatibility Routing Results

This folder will hold compact paper-facing H002 summaries if the branch is promoted.

## Current Status

```text
status = main_validation_claim_table_locked_no_final_test_results
paper_level_ready = false
grouped_holdout_metrics_exist = true_internal_candidate_pool_only
calibration_metrics_exist = false
row_level_runtime_outputs_exist = true
schema_audit_runtime_outputs_exist = true
grouped_split_runtime_outputs_exist = true
grouped_eval_protocol_exists = true
grouped_eval_runtime_outputs_exist = true
grouped_eval_result_review_exists = true
relative_vertical_failure_analysis_exists = true
grouped_eval_feature_extractor_repair_exists = true
claim_boundary_review_exists = true
official_validation_test_protocol_plan_exists = true
official_source_inventory_exists = true
official_candidate_materialization_protocol_exists = true
official_candidate_materialization_runtime_exists = true
official_candidate_materialization_schema_audit_exists = true
official_candidate_materialization_schema_audit_caveat = support_contact_predicate_class_pair_shortcut
official_metric_protocol_freeze_exists = true
official_metric_runner_outputs_exist = true
official_validation_metric_exists = true_not_promoted
official_metric_result_review_exists = true
paper_level_experiment_execution_gate = passed_with_caveats
official_metric_claim_boundary_lock_exists = true
paper_table_draft_allowed = true
paper_table_skeleton_exists = true
paper_table_skeleton_ready_for_review = true
paper_table_skeleton_review_exists = true
principled_structure = true
bounded_mechanism_evidence_only = true
principled_design_gap_plan_exists = true
selected_gap = harder_support_contact_route
support_contact_harder_route_protocol_exists = true
support_contact_harder_route_source_inventory_exists = true
support_contact_harder_route_materialization_plan_exists = true
support_contact_harder_route_docker_materialization_exists = true
support_contact_harder_route_schema_shortcut_audit_exists = true
support_contact_harder_route_metric_protocol_exists = true
support_contact_harder_route_train_eval_alignment_exists = true
support_contact_harder_route_train_eval_feature_parity = ready_with_derived_proxy_mappings
support_contact_harder_route_metric_runner_outputs_exist = true
support_contact_harder_route_metric_expectation_passed = false
source_deployable_experiment = deferred
source_reranking_validation_table_position = main_validation_benchmark
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
official_test_benchmark_claim_allowed = false
open3dsg_source_boundary = open_vocabulary_source_closed_vocabulary_3dssg_mapping
h003_embedding_extension_in_main_claim_now = false
h003_embedding_extension_future_optional = true
checkpoint_reproduction_is_sufficient_for_test_recall = false
prediction_only_test_scan_export_is_sufficient_for_test_recall = false
p_obs_p_rel_branch = deferred
final_paper_result_promotion = not_yet
paper_metric_exists = false
```

## Boundary

Do not store large row-level JSONL dumps, point clouds, model caches, feature caches, or packet assets here.

Current row-level materialization outputs are intentionally stored under:

```text
experiments/H002_compatibility_routing/materialization/latest/
```

They are not compact paper-facing results and should not be copied here until a later schema/shortcut audit and grouped evaluation produce compact summaries.

Current support/contact hard-route materialization and schema/shortcut audit
outputs are intentionally stored under:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest/
```

The schema audit passed with warnings, but it is still not a compact paper-facing
result. The high `predicate x class-pair` shortcut risk means support/contact is
not promoted as a solved family.

The support/contact hard-route metric protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit/
```

This is still not a metric result. The next required gate is train/eval feature
alignment before any support/contact hard-route metric runner can produce compact
results.

The support/contact hard-route train/eval alignment artifact now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze/
```

It produced runner-ready train/dev inputs.

Support/contact hard-route metric runner outputs now exist under:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
```

They are runtime metric outputs, not compact paper-facing results. The stage
review artifact exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment/
```

Current runner snapshot: internal dev `M4_TxG_compatibility` AUROC `0.721356`,
official validation `M4_TxG_compatibility` AUROC `0.077539`, wrong-`T` AUROC
`0.922461`, validation errors `0`. This fails the support/contact hard-route
metric expectation, so no compact paper-facing result should be copied here
until result review resolves or freezes the failure boundary.

Current schema-audit runtime outputs are intentionally stored under:

```text
experiments/H002_compatibility_routing/schema_audit/latest/
```

They confirm materialization schema readiness but are still not grouped metrics or paper-facing result summaries.

Current grouped-split runtime outputs are intentionally stored under:

```text
experiments/H002_compatibility_routing/splits/latest/
```

They assign the `6952` internal H002 candidate rows and `3684` `cv_group_id` groups to `internal_train`, `internal_dev`, and `internal_heldout`. They are protocol artifacts, not paper-facing result metrics.

The grouped evaluation protocol exists under the H002 hypothesis folder:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split/
```

Grouped evaluation runtime outputs now exist under:

```text
experiments/H002_compatibility_routing/evaluation/latest/
```

Those metrics are internal candidate-pool grouped holdout metrics. They are not official validation/test metrics and should not be copied here as compact paper-facing summaries until claim-lock and paper-result promotion stages pass.

Grouped evaluation result review exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner/
```

After feature extractor repair, the review keeps `size_relative`, `relative_vertical`, and `relative_horizontal` as claim-supporting internal evidence, while `support_contact` remains partial/challenging.

Relative-vertical failure analysis exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review/
```

It diagnoses the grouped failure as a feature-extraction issue in the runtime runner, not as paper-ready negative evidence.

Grouped-eval feature extractor repair exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis/
```

It confirms repaired internal heldout `M4_TxG_compatibility` AUROC `0.984976`, with `relative_vertical` restored to AUROC `0.999921`. These are still internal candidate-pool metrics, not official validation/test or paper-level metrics.

Repaired grouped-eval claim-boundary review exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review/
```

It allows only hypothesis-stage internal `C_e` compatibility claims and blocks
official validation/test, calibrated `p_rel/p_obs`, solved support/contact,
all-relation generalization, and aggregate-only claims. No compact paper-facing
H002 result has been promoted here yet.

Support/contact hard-route source inventory exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol/
```

It is not a compact paper result. It records that official validation
support/contact has enough semseg/PLY/mesh/normal/segment source material for a
richer `G_e` materializer, while the current support/contact claim remains
diagnostic because predicate/class-pair shortcuts still explain too much.

Support/contact hard-route materialization plan exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory/
```

It is also not a compact paper result. It freezes the next Docker materializer
contract and the `model_safe_main_no_class` policy for richer support/contact
`G_e`; no rows, metrics, or paper-facing results are stored here from that stage.

Support/contact hard-route Docker materialization outputs now exist under:

```text
experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
```

They are row-level runtime outputs, not compact paper-facing results. The stage
review artifact exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan/
```

The run produced `3178` rows, `1589` groups, `43` richer `G_e` features, and `0`
validation errors. It still must pass schema/shortcut audit and metric review
before anything can be copied here as a compact paper-facing result.

Official validation/test protocol plan exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review/
```

It records split inventory and protocol policy only. It does not promote
official validation metrics. Local `3DSSG_subset` validation has 548 scans /
11,254 relations; local test labels were not observed.

Official source inventory exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan/
```

It confirms validation GT/object geometry candidate material and read-only
VL-SAT/Open3DSG source candidate availability, but it still does not create a
compact paper-facing result. `relative_horizontal` and `size_relative` require
H002-specific `G_e` because H001 geometry verification marks those families as
unsupported.

Official candidate materialization protocol exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory/
```

It freezes row schema, family route policy, source bridge policy, blocked-field
rules, and audit contract. It still does not create compact paper-facing metrics
or materialized official rows. Future compact summaries can be placed here only
after Docker official materialization, schema/shortcut audit, metric freeze, and
metric review pass.

Official materialization runtime outputs now exist under:

```text
experiments/H002_compatibility_routing/official_materialization/latest/
```

They include `23062` candidate/model-safe/hidden rows and `0` validation errors.
These are row-level runtime outputs, not compact paper-facing results. Do not
copy them into `results/`.

Official materialization schema-audit runtime outputs now also exist under:

```text
experiments/H002_compatibility_routing/official_schema_audit/latest/
```

The audit has `0` schema violations, `0` blocked field hits, `0` runtime
validation errors, complete model-safe/hidden alignment for `23062` rows, and
`0` control-readiness blockers. It also records one shortcut caveat:
`support_contact` `predicate_x_class_pair` majority accuracy `0.993707`.

This folder should receive compact paper-facing summaries only after metric
protocol freeze, official metric run, leakage/control review, and claim-lock
promotion pass. The schema audit itself is a gate artifact, not a paper result.

Official metric protocol freeze now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit/
```

It is still not a paper-facing result. It freezes official validation as
eval-only, primary `macro_family_AUROC`, secondary weighted/overall metrics,
required controls, and exclusion of `Z_e`, `Q_e`, H001 `p_geom_valid`, and hidden
construction fields from main `C_e`.

Official metric runner outputs now exist under:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

They include official validation metrics but are not promoted paper-facing
results. Current runner snapshot: M4 macro-family AUROC `0.8355465299908279`,
weighted-family AUROC `0.7207808044279794`, overall AUROC `0.724835499373417`,
and validation errors `0`. Caveats remain: `support_contact` is challenging
with M4 AUROC `0.6317116456316851`, and `relative_horizontal` needs frame-control
review because horizontal frame-swap delta AUROC is `0.03814880004643195`.

Compact paper-facing summaries should still wait for the bounded paper-table
skeleton stage. The claim-boundary lock is complete, but final paper result
promotion is not complete.

Official metric result review now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
```

The review allows moving to claim-boundary lock but still does not promote a
paper-facing result. Main paper-candidate families are `relative_vertical` and
`size_relative`; `relative_horizontal` has a frame-control caveat; `support_contact`
is diagnostic/challenging only.

Official metric claim-boundary lock now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review/
```

The lock allows a bounded paper-table draft. `relative_vertical` and
`size_relative` are primary mechanism rows, `relative_horizontal` is a caveated
frame-aware row, and `support_contact` is a diagnostic/failure-taxonomy row.
Final paper result promotion, official test claims, source reranking claims,
calibrated `p_rel`/`p_obs` claims, all-relation claims, and SOTA/full-3DSSG
wording remain blocked.

Bounded paper-table skeleton now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock/
```

Skeleton status: ready for review, not final promotion. The primary mechanism
macro uses `relative_vertical + size_relative`; `relative_horizontal` remains
caveated; `support_contact` remains diagnostic.

Paper table skeleton review now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock/
```

Review status: the structure is principled and natural, but the current table is
bounded mechanism evidence only. It is not a standalone final paper result
because the primary evidence is too clean/signed-comparison-heavy. The next step
is a harder-route or source-deployable gap plan.

Principled design gap plan now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review/
```

The selected next path is a support/contact harder-route protocol. This is still
not a paper metric. It is a plan to repair the evidence difficulty gap before
paper-result promotion.

Support/contact harder-route protocol now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan/
```

This protocol is still not a compact result. It locks `standing on` / `lying on`
as the main hard-route predicates, keeps `supported by` diagnostic, and selects
source inventory as the next step.

Test benchmark source resolution now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight/
```

This is a blocked gate, not a compact result. It confirms that 3RScan has a
scan-level test split, but H002 still lacks confirmed 3DSSG relation-test labels,
accepted official evaluation-server route, and exact test source predictions.
Validation source-reranking output remains appendix/secondary analysis only.

External provenance request packet now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution/
```

This is not a compact paper result. It records the questions and source evidence
needed to confirm whether a test benchmark is possible. The folder should remain
empty of paper-facing H002 test metrics until a response/provenance artifact is
ingested and a single final test protocol is frozen.

External response ingestion now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request/
```

This is also not a compact paper result. It found no response/provenance artifact
and keeps official test metrics blocked. Do not add H002 test benchmark summaries
to this results folder until official provenance is positive and a single final
test protocol is frozen.

Validation-only position lock now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response/
```

This locks current H002 source-reranking metrics as validation-level custom
protocol evidence. They may be summarized only as appendix/secondary analysis,
not as official test or SOTA benchmark results. Open3DSG should be described as
an open-vocabulary source evaluated through closed-vocabulary 3DSSG mapping.

Post-validation path decision now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision/
```

This supersedes the appendix-only position. Compact H002 validation summaries may
be prepared as main validation benchmark material, with explicit captions that
state official 3DSSG validation split, not official test. Do not store or claim
official-test results here.

Main validation claim/table lock now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision/
```

This is still not a compact table itself. The next step should write
caption-ready compact rows under this results root or an H002 artifact root,
depending on the promotion decision.

Expected future compact files include:

- route metric summaries,
- control metric summaries,
- aggregate metric summaries,
- split manifests,
- leakage-audit summaries,
- calibration summaries if `p_rel` / `p_obs` claims are pursued,
- claim-lock manifests,
- reviewed bounded paper-table skeletons.

Row-level runtime outputs should stay under `experiments/H002_compatibility_routing/` or ignored runtime roots, then be summarized here only after validation.
