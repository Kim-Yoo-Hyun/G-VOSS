# H002 Compatibility Routing Results

This folder will hold compact paper-facing H002 summaries if the branch is promoted.

## Current Status

```text
status = official_metric_result_review_exists_no_paper_results
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
paper_metric_exists = false
```

## Boundary

Do not store large row-level JSONL dumps, point clouds, model caches, feature caches, or packet assets here.

Current row-level materialization outputs are intentionally stored under:

```text
experiments/H002_compatibility_routing/materialization/latest/
```

They are not compact paper-facing results and should not be copied here until a later schema/shortcut audit and grouped evaluation produce compact summaries.

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

Compact paper-facing summaries should still wait for official metric result
review and claim-boundary lock.

Official metric result review now exists under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner/
```

The review allows moving to claim-boundary lock but still does not promote a
paper-facing result. Main paper-candidate families are `relative_vertical` and
`size_relative`; `relative_horizontal` has a frame-control caveat; `support_contact`
is diagnostic/challenging only.

Expected future compact files include:

- route metric summaries,
- control metric summaries,
- aggregate metric summaries,
- split manifests,
- leakage-audit summaries,
- calibration summaries if `p_rel` / `p_obs` claims are pursued,
- claim-lock manifests.

Row-level runtime outputs should stay under `experiments/H002_compatibility_routing/` or ignored runtime roots, then be summarized here only after validation.
