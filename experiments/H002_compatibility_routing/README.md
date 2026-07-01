# H002 Compatibility Routing Experiment

This is the Docker promotion skeleton for H002:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## Current Status

```text
status = official_metric_result_review_ready_with_boundaries_no_paper_result
paper_level_ready = false
docker_preflight_run = true
route_materialization_run = true
materialization_schema_audit_run = true
grouped_split_protocol_run = true
grouped_eval_protocol_run = true
grouped_eval_runner_run = true
grouped_holdout_run = true_internal_candidate_pool_only
official_validation_usage = false
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
h001_source_inventory_read_only = true
next_todo = compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
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

No paper-level H002 metric has been produced from this folder.

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

H001 artifacts are read-only references if used. This folder must not modify H001 outputs.

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
