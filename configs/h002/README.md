# H002 Docker Config

This folder will own Docker configuration for H002 compatibility-routing promotion.

## Current Status

```text
status = main_validation_claim_table_locked_test_blocked
paper_metric_ready = false
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
official_test_benchmark_claim_allowed = false
open3dsg_source_boundary = open_vocabulary_source_closed_vocabulary_3dssg_mapping
h003_embedding_extension_in_main_claim_now = false
h003_embedding_extension_future_optional = true
checkpoint_reproduction_is_sufficient_for_test_recall = false
prediction_only_test_scan_export_is_sufficient_for_test_recall = false
final_paper_result_promotion = not_yet
next_todo = compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock
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
| `h002-calibration` | optional calibration/selective-risk evaluation for `p_rel` / `p_obs` |

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
`h002-source-rerank-metric-runner`.

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

Official metric result review, official metric claim-boundary lock, source-reranking result review, and source-reranking claim-boundary lock artifacts now exist under the H002 hypothesis folder. Do not add calibration or `p_rel`/`p_obs` services to paper-result use until their own protocol, Docker run, review, and claim-lock artifacts exist.

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

The next config-level step should materialize compact table rows from existing
validation artifacts. Do not open an official-test service.

H001 artifacts must be mounted read-only if referenced.
