# H001 Geometry Reliability Experiment

Last updated: 2026-06-05

This is the first paper-body experiment workflow for H001. It is Docker-based by rule.

## Scope

Current executable sources:

- `VL-SAT` / `vlsat_closed_set`
- `Open3DSG` / `open3dsg_ov`

Selected top-tier expansion:

- Open3DSG second-source adapter result after Dockerized checkpoint reproduction; checkpoint plan, `training_repro` metadata/split staging, full payload staging, train/validation views, explicit train/validation preprocess filtering, official BLIP TopK5/scales3 feature dump, Docker feature audit, avg-BLIP checkpoint reproduction, checkpoint selection, eval preflight, H001 held-out eval feature-cache generation, raw-dump identity checklist, adapter export, geometry join, metric eval, predicate-family/denominator metric-scope policy, pre-metric failure-analysis schema, synthetic failure row-generator smoke, real failure-analysis rows, qualitative case inspection, paper caveat wording, Table 6 hook, and subgraph bootstrap CI are ready.
- Open3DSG caveat-reduction plan is frozen under `sources/open3dsg/caveat_reduction_plan/`. Retry order is R1 exact non-averaged BLIP route, R2 H001 covered-loadable context retry toward `388/388`, and R3 attachment G5d only after the Open3DSG decisions are resolved or waived. R1 completed with exit `0` on 2026-06-04 KST and Docker checkpoint selection selected the official non-avg checkpoint `epoch=13-step=13104.ckpt` from MLflow run `25da9c4c00214f3b880cedbb2a124177` using train-dev `val/loss=0.5724539160728455`. The existing avg-BLIP route still has better train-dev `val/loss=0.32881081104278564` for the historical 127-scan comparison. The non-avg downstream branch is complete under `sources/open3dsg/non_avg/`; paper-facing Open3DSG primary evidence now comes from the full-validation 548/548 recovery branch. Current decomposition records attachment Open3DSG missing exact-label GT rows as 199 total: 23 from missing preprocessed H001 contexts and 176 from absent Open3DSG candidate pairs.
- Open3DSG non-avg downstream branch is ready without overwriting avg-BLIP artifacts. Raw stream completed 19,162 rows and 377/377 batches, then the process exited `137` after finalization. Manual downstream services passed: raw-dump identity, adapter export, geometry join, metric eval, bootstrap CI, and Table 6/caveat report. Key non-avg metrics: semantic_only R@50/R@100 `0.4310/0.5320`, Violation@50/@100 `0.1395/0.1256`; probabilistic_recalibrated R@50/R@100 `0.3945/0.5639`, Violation@50/@100 `0.0570/0.0782`; rule_verified_point_subtype R@50/R@100 `0.4507/0.5481`, Violation@50/@100 `0.0/0.0`; family_specific control R@50/R@100 `0.4750/0.6047`, Violation@50/@100 `0.0243/0.0310`.
- `relative_horizontal` is now a separate scope-expansion validation track under `sources/relative_horizontal/`. The no-training/no-inference Docker scope audit is ready, with 3,570 candidate GT rows and source rows for VL-SAT / Open3DSG, but current verification status remains unsupported. The Docker coordinate audit and bucket inspection are also ready and currently blocked: best scan-frame macro strict purity is 0.7725, `front`/`behind` strict purity is 0.7445, inverse consistency is 1.0, wrong-frame gap is 0.1231, and `front`/`behind` ambiguity buckets remain substantial. Recommendation is `do_not_promote_relative_horizontal_to_main_claim`. Current AAAI-path decision is to freeze this as appendix/limitation evidence and not run expanded-family metrics. This does not change the current main paper claim. It can only be promoted after coordinate-frame semantics, denominator audit, verifier policy, calibration, controls, source metrics, bootstrap CI, and failure/audit evidence reach the same standard as the current H001 families.
- `attachment_deferred` is now the preferred future relation-family upgrade under `sources/attachment_deferred/`, not current metric evidence. Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry run, G1c point/surface estimator validation, G2 conservative verifier-policy design, G3 train-dev calibration/counterfactual route, G4 GT policy smoke, G4b error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a pooled strict calibration fit, G5b bounded source scoring preflight, and G5c full-source protocol freeze are complete with status `attachment_deferred_full_source_protocol_frozen_no_metrics`: it adds 967 GT rows (`attached to` 808, `hanging on` 126, `connected to` 33), with candidate source rows for VL-SAT 77,748 and Open3DSG 57,300, and current verification status `unsupported` for both sources. G4c freezes 325 strict calibration rows, G5a fits model `h001-attachment-deferred-p-geom-valid-strict-v1`, G5b scores 120 scan-diverse bounded source rows with 0 validation errors, and G5c freezes 69 deterministic full-source shards for 135,048 rows plus source-specific covered denominators: VL-SAT 967/967 and Open3DSG 768/967. This is still not source metric evidence; full-source scoring, source metrics, controls, bootstrap CI, and completed visual audit do not exist yet. Main AAAI claim promotion requires explicit final user confirmation.
- Qwen-VL third semantic source / modern VLM extension contract is ready under `sources/qwen_vl/`; recommended small model ladder is Qwen3-VL-4B first, Qwen2.5-VL-3B stable fallback, and Qwen3-VL-2B parser-smoke candidate. Frozen input JSON Schema, output JSONL contract, contract-only validator/parser skeleton, non-held-out tiny pilot scope, runtime model-lock plan, tiny-pilot pair-crop rendering path, model-cache verification, runtime preflight, 3-row tiny inference smoke, runtime raw-response validation, full-source promotion plan, full-source input audit, full-source crop preflight, and full-source inference runner plan are recorded. Current full-source input audit has 77,748 universe rows, 33,384 inferable input rows, 44,364 missing rows, and 134 shards. All-scope crop preflight passed for 33,384 input rows / 11,128 unique pair crops / 0 errors. Runner plan freezes 134 shard commands/resume policy; shards 0000-0013 are complete with 3,500 parsed rows, and run id `20260527_023111` stopped at shard 0014 because the GPU guard observed utilization 36% against the 35% threshold. This is not a replacement for VL-SAT or Open3DSG evidence, and no full Qwen paper-metric evaluation has run.

Current method framing:

```text
calibrated geometry-consistency evaluation and re-ranking framework
```

## Full Official Validation Transition

2026-06-05 decision update: the paper-facing primary route is now the full
official `3DSSG_subset` validation split. VL-SAT full-validation is the
controlled-anchor primary result. Open3DSG
`sources/open3dsg/full_validation/recovery_relaxed_views_min2/` is the primary
full-denominator Open3DSG branch; the original 533/548 covered branch remains a
sensitivity / unmodified-source-route check. The existing 127-scan hardened
results are historical/sensitivity evidence, not the main table route.

Target full-validation scope:

| Item | Count |
| --- | ---: |
| validation scans | 157 |
| contexts | 548 |
| GT-positive directed pairs | 7,720 |
| candidate directed pairs | 36,808 |
| GT rows | 11,254 |
| H001-family GT rows | 3,972 |
| expected VL-SAT prediction rows | 957,008 |
| `support_contact` | 1,816 |
| `proximity` | 1,766 |
| `relative_vertical` | 390 |

Method provenance rule: final predicate-family mapping, hard-rule policies,
counterfactual construction, and `p_geom_valid` calibration must be described
as train/train-dev-derived and frozen before validation source-result
reporting. H001-Mini is hypothesis/feasibility evidence, not a paper metric
split. Full-validation results require separate VL-SAT and Open3DSG output
paths, fresh geometry joins, metrics, controls, bootstrap CI, and caveat
wording before any AAAI table or main claim is rewritten.

Current transition status:

```text
full_official_validation_scope_contract_ready_no_metric_execution
vlsat_full_validation_metric_bundle_ready
vlsat_full_validation_failure_analysis_ready
open3dsg_full_validation_metric_bundle_ready_with_caveats
open3dsg_full_validation_recovery_relaxed_views_min2_metric_bundle_ready
open3dsg_full_validation_recovery_failure_case_inspection_ready
paper_full_validation_primary_route_selected_recovery_branch
```

Docker `full_validation_scope_contract` generated the scope-freeze artifact at:

```text
experiments/H001_geom_reliability/full_validation_transition/scope_contract/
```

It records raw payload readiness 157/157, existing VL-SAT hardened staged root
127/157, existing Open3DSG H001 runtime views 127/157, existing Open3DSG H001
runtime preprocess 377/548, and separate output paths for the full-validation
rerun. This is not metric evidence.

VL-SAT full-validation staging and runtime preflight are now Docker-ready:

- staged root: `local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT`
- stage artifact: `sources/vlsat/full_validation/stage/`
- runtime record: `sources/vlsat/full_validation/runtime_record/`
- raw preflight: `sources/vlsat/full_validation/raw_preflight/`
- result: 157/157 faithful staged scans, 16/16 checkpoint files, raw preflight
  `ready_to_run`, 0 errors, and 1 expected legacy import-shim warning.

The VL-SAT full-validation metric bundle is now ready under
`sources/vlsat/full_validation/`. Run record:
`sources/vlsat/full_validation/raw/run_20260604_204428.md`. Completed artifacts:
raw dump/export, ground-truth JSONL, geometry join, metrics, controls, GT
verifier check, VL-SAT-only bootstrap CI, failure-analysis rows, and
deterministic qualitative failure-case inspection under the same
full-validation scope. Failure rows: 59,841; selected qualitative cases: 36.
Key metrics:

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| probabilistic_recalibrated | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| rule_verified_point_subtype | 0.9257 | 0.9627 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.9288 | 0.9683 | 0.0206 | 0.0333 |

The Open3DSG full-validation metric bundle is also ready under
`sources/open3dsg/full_validation/`. It was generated under separate output
paths and does not overwrite the existing avg-BLIP or non-avg hardened
branches. Completed gates: payload/views/preprocess coverage audit, recovery
attempt for missing contexts, covered-scope feature seed/audit, selected
checkpoint raw dump, raw-dump identity, adapter export, geometry join,
metrics/controls, bootstrap CI, failure rows, and Table 6/caveat regeneration.

Open3DSG full-validation coverage and row counts:

- views: 157/157
- preprocess: 533/548, with 15 missing contexts after recovery attempts
- covered-scope features: 533/533 complete feature ids
- raw stream: 26,746 rows / 533 completed batches
- adapter: 690,924 prediction rows
- geometry: 690,924 verification rows, 159,444 geometry-checkable H001-family rows
- failure rows: 81,448
- bootstrap CI: ready with 1,000 subgraph resamples

Open3DSG full-validation metrics:

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.4043 | 0.5111 | 0.1387 | 0.1242 |
| probabilistic_recalibrated | 0.3943 | 0.5685 | 0.0590 | 0.0807 |
| rule_verified_point_subtype | 0.4242 | 0.5320 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.4612 | 0.5999 | 0.0265 | 0.0332 |

Open3DSG full-validation caveats: the existing metric bundle uses the selected
official non-avg BLIP checkpoint, the raw process exited `137` after stream
finalization, and 15 contexts remained missing after the first preprocessing
recovery attempts. A separate missing-15 recovery branch is now active under
`sources/open3dsg/full_validation/preprocess_recovery_relaxed_views_min2/`.
It diagnoses the Open3DSG source drop as the hard-coded fewer-than-4-visible-
objects preprocess gate, recovers all 15 contexts through `min_visible=2` plus
relaxed view-generation for the final two scans, and passes preprocess audit
at 548/548. The recovery downstream branch is now complete under
`sources/open3dsg/full_validation/recovery_relaxed_views_min2/`: feature audit
548/548, raw stream exit `0`, 26,938 raw rows / 548 completed batches, adapter
695,916 prediction rows, geometry 695,916 rows, metrics/controls, bootstrap CI,
82,155 failure rows, and Table 6/caveat regeneration are ready. Recovery
metrics: semantic_only R@50/R@100 `0.4096/0.5161`, V@50/@100
`0.1386/0.1242`; probabilistic_recalibrated R@50/R@100 `0.3975/0.5723`,
V@50/@100 `0.0606/0.0811`; rule_verified_point_subtype R@50/R@100
`0.4295/0.5368`, V@50/@100 `0.0/0.0`; family_specific control R@50/R@100
`0.4658/0.6047`, V@50/@100 `0.0286/0.0341`. This branch removes the
missing-context denominator caveat and is the selected paper-facing primary
Open3DSG full-validation route, but it must be reported as a recovery-policy
variant because it relaxes the visible-object gate and regenerates relaxed views
for two scans. Recovery failure-case inspection is ready with 36 selected
high-severity cases: 25/36 demoted by geometry-aware reranking, 11/36 promoted
or retained, and 8/36 violated rows with `p_geom_valid > 0.9`.

VL-SAT and Open3DSG full-validation metric evidence now define the paper-facing
primary route. The full-validation failure-taxonomy artifacts now also exist
for both sources. The 533/548 Open3DSG covered branch remains a sensitivity /
unmodified-source-route check.

Transition record:

```text
experiments/H001_geom_reliability/full_validation_transition/report.md
```

## What This Stage Does

This stage reads locked hypothesis artifacts, validates fixed counts, records input hashes/row counts, generates paper-facing tables/report files, records the Dockerized Open3DSG checkpoint reproduction plan, stages the Open3DSG `training_repro` metadata/split root, and tracks the Dockerized Open3DSG second-source reproduction pipeline. Open3DSG paper-facing metric promotion is now enabled only within measured H001 families and closed-set/GT-object scope.
It also computes Dockerized subgraph bootstrap confidence intervals for the same VL-SAT and Open3DSG metric rows.

Generated outputs:

- `tables/table1_main_prediction.*`
- `tables/table2_controls.*`
- `tables/table3_gt_verifier.*`
- `tables/table4_audit.*`
- `tables/table5_claim_boundary.*`
- `tables/table6_cross_source_status.*`
- `figures/figure_specs.*`
- `sources/vlsat/locked_inputs.json`
- `sources/open3dsg/checkpoint_plan.*`
- `sources/open3dsg/Dockerfile.repro`
- `sources/open3dsg/compose.open3dsg.yaml`
- `sources/open3dsg/commands.open3dsg.md`
- `sources/open3dsg/post_dump_handoff/manifest.json`
- `sources/open3dsg/post_dump_handoff/commands.md`
- `sources/open3dsg/post_dump_handoff/report.md`
- `sources/open3dsg/checkpoint_selection/selection_policy.json`
- `sources/open3dsg/checkpoint_selection/record_template.json`
- `sources/open3dsg/checkpoint_selection/manifest.json`
- `sources/open3dsg/checkpoint_selection/commands.md`
- `sources/open3dsg/checkpoint_selection/report.md`
- `sources/open3dsg/raw_dump_identity/checklist.json`
- `sources/open3dsg/raw_dump_identity/manifest.json`
- `sources/open3dsg/raw_dump_identity/commands.md`
- `sources/open3dsg/raw_dump_identity/report.md`
- `sources/open3dsg/metric_scope/predicate_mapping.json`
- `sources/open3dsg/metric_scope/denominator_policy.json`
- `sources/open3dsg/metric_scope/manifest.json`
- `sources/open3dsg/metric_scope/commands.md`
- `sources/open3dsg/metric_scope/report.md`
- `sources/open3dsg/failure_analysis/schema.json`
- `sources/open3dsg/failure_analysis/taxonomy.json`
- `sources/open3dsg/failure_analysis/aggregation_plan.json`
- `sources/open3dsg/failure_analysis/report.md`
- `sources/open3dsg/failure_analysis_generator_smoke/rows.jsonl`
- `sources/open3dsg/failure_analysis_generator_smoke/summary.json`
- `sources/open3dsg/failure_analysis_generator_smoke/manifest.json`
- `sources/open3dsg/failure_analysis_generator_smoke/report.md`
- `sources/open3dsg/failure_rows/rows.jsonl`
- `sources/open3dsg/failure_rows/summary.json`
- `sources/open3dsg/failure_rows/manifest.json`
- `sources/open3dsg/failure_rows/report.md`
- `sources/open3dsg/metric_join_contract/input_contract.json`
- `sources/open3dsg/metric_join_contract/output_contract.json`
- `sources/open3dsg/metric_join_contract/metrics.json`
- `sources/open3dsg/metric_join_contract/manifest.json`
- `sources/open3dsg/metric_join_contract/commands.md`
- `sources/open3dsg/metric_join_contract/report.md`
- `sources/open3dsg/adapter/predictions.jsonl`
- `sources/open3dsg/adapter/manifest.json`
- `sources/open3dsg/adapter/report.md`
- `sources/open3dsg/geometry/verification.jsonl`
- `sources/open3dsg/geometry/manifest.json`
- `sources/open3dsg/geometry/report.md`
- `sources/open3dsg/metrics/metrics.json`
- `sources/open3dsg/metrics/report.md`
- `sources/open3dsg/caveat_reduction_plan/manifest.json`
- `sources/open3dsg/caveat_reduction_plan/retry_plan.json`
- `sources/open3dsg/caveat_reduction_plan/commands.md`
- `sources/open3dsg/caveat_reduction_plan/report.md`
- `sources/open3dsg/training_repro/manifest.json`
- `sources/open3dsg/training_repro/report.md`
- `sources/open3dsg/status.json`
- `sources/open3dsg/table6_hook.json`
- `sources/relative_horizontal/README.md`
- `sources/relative_horizontal/scope_audit/manifest.json`
- `sources/relative_horizontal/scope_audit/label_counts.json`
- `sources/relative_horizontal/scope_audit/report.md`
- `sources/relative_horizontal/coordinate_audit/manifest.json`
- `sources/relative_horizontal/coordinate_audit/frame_metrics.json`
- `sources/relative_horizontal/coordinate_audit/records.jsonl`
- `sources/relative_horizontal/coordinate_audit/ambiguity_buckets.json`
- `sources/relative_horizontal/coordinate_audit/report.md`
- `sources/relative_horizontal/bucket_inspection/manifest.json`
- `sources/relative_horizontal/bucket_inspection/summary.json`
- `sources/relative_horizontal/bucket_inspection/examples.jsonl`
- `sources/relative_horizontal/bucket_inspection/report.md`
- `sources/attachment_deferred/README.md`
- `sources/attachment_deferred/scope_audit/manifest.json`
- `sources/attachment_deferred/scope_audit/label_counts.json`
- `sources/attachment_deferred/scope_audit/evidence_schema.json`
- `sources/attachment_deferred/scope_audit/report.md`
- `sources/attachment_deferred/evidence_extractor/manifest.json`
- `sources/attachment_deferred/evidence_extractor/extractor_contract.json`
- `sources/attachment_deferred/evidence_extractor/output_schema.json`
- `sources/attachment_deferred/evidence_extractor/field_catalog.json`
- `sources/attachment_deferred/evidence_extractor/subtype_policy.json`
- `sources/attachment_deferred/evidence_extractor/extraction_plan.json`
- `sources/attachment_deferred/evidence_extractor/validation_plan.json`
- `sources/attachment_deferred/evidence_extractor/example_row.json`
- `sources/attachment_deferred/evidence_extractor/report.md`
- `sources/attachment_deferred/extractor_dry_run/rows.jsonl`
- `sources/attachment_deferred/extractor_dry_run/manifest.json`
- `sources/attachment_deferred/extractor_dry_run/summary.json`
- `sources/attachment_deferred/extractor_dry_run/validation.json`
- `sources/attachment_deferred/extractor_dry_run/report.md`
- `sources/attachment_deferred/point_surface_validation/rows.jsonl`
- `sources/attachment_deferred/point_surface_validation/diagnostics.jsonl`
- `sources/attachment_deferred/point_surface_validation/manifest.json`
- `sources/attachment_deferred/point_surface_validation/summary.json`
- `sources/attachment_deferred/point_surface_validation/validation.json`
- `sources/attachment_deferred/point_surface_validation/report.md`
- `sources/attachment_deferred/verifier_policy/manifest.json`
- `sources/attachment_deferred/verifier_policy/verifier_policy.json`
- `sources/attachment_deferred/verifier_policy/decision_schema.json`
- `sources/attachment_deferred/verifier_policy/threshold_plan.json`
- `sources/attachment_deferred/verifier_policy/reason_codes.json`
- `sources/attachment_deferred/verifier_policy/calibration_plan.json`
- `sources/attachment_deferred/verifier_policy/commands.md`
- `sources/attachment_deferred/verifier_policy/report.md`
- `sources/attachment_deferred/calibration_counterfactuals/manifest.json`
- `sources/attachment_deferred/calibration_counterfactuals/positive_seeds.jsonl`
- `sources/attachment_deferred/calibration_counterfactuals/counterfactual_seeds.jsonl`
- `sources/attachment_deferred/calibration_counterfactuals/split_plan.json`
- `sources/attachment_deferred/calibration_counterfactuals/counterfactual_plan.json`
- `sources/attachment_deferred/calibration_counterfactuals/policy_smoke_plan.json`
- `sources/attachment_deferred/calibration_counterfactuals/gt_eval_inputs.json`
- `sources/attachment_deferred/calibration_counterfactuals/threshold_freeze_protocol.json`
- `sources/attachment_deferred/calibration_counterfactuals/commands.md`
- `sources/attachment_deferred/calibration_counterfactuals/report.md`
- `sources/attachment_deferred/gt_policy_smoke/manifest.json`
- `sources/attachment_deferred/gt_policy_smoke/summary.json`
- `sources/attachment_deferred/gt_policy_smoke/validation.json`
- `sources/attachment_deferred/gt_policy_smoke/policy_smoke_decisions.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_evidence_rows.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_evidence_diagnostics.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_policy_decisions.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_eval_rows.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/visual_sanity_plan.json`
- `sources/attachment_deferred/gt_policy_smoke/commands.md`
- `sources/attachment_deferred/gt_policy_smoke/report.md`
- `sources/attachment_deferred/error_visual_sanity/manifest.json`
- `sources/attachment_deferred/error_visual_sanity/summary.json`
- `sources/attachment_deferred/error_visual_sanity/review_cases.jsonl`
- `sources/attachment_deferred/error_visual_sanity/visual_queue.jsonl`
- `sources/attachment_deferred/error_visual_sanity/calibration_filter.jsonl`
- `sources/attachment_deferred/error_visual_sanity/guide.md`
- `sources/attachment_deferred/error_visual_sanity/commands.md`
- `sources/attachment_deferred/error_visual_sanity/report.md`
- `sources/attachment_deferred/strict_filter_freeze/manifest.json`
- `sources/attachment_deferred/strict_filter_freeze/summary.json`
- `sources/attachment_deferred/strict_filter_freeze/freeze_policy.json`
- `sources/attachment_deferred/strict_filter_freeze/strict_calibration_rows.jsonl`
- `sources/attachment_deferred/strict_filter_freeze/excluded_rows.jsonl`
- `sources/attachment_deferred/strict_filter_freeze/commands.md`
- `sources/attachment_deferred/strict_filter_freeze/report.md`
- `sources/attachment_deferred/calibration_fit/manifest.json`
- `sources/attachment_deferred/calibration_fit/model.json`
- `sources/attachment_deferred/calibration_fit/metrics.json`
- `sources/attachment_deferred/calibration_fit/scores.jsonl`
- `sources/attachment_deferred/calibration_fit/commands.md`
- `sources/attachment_deferred/calibration_fit/report.md`
- `sources/attachment_deferred/source_scoring_preflight/manifest.json`
- `sources/attachment_deferred/source_scoring_preflight/summary.json`
- `sources/attachment_deferred/source_scoring_preflight/source_rows.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/evidence_rows.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/diagnostics.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/scored_rows.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/commands.md`
- `sources/attachment_deferred/source_scoring_preflight/report.md`
- `sources/attachment_deferred/full_source_protocol/manifest.json`
- `sources/attachment_deferred/full_source_protocol/protocol.json`
- `sources/attachment_deferred/full_source_protocol/denominator_audit.json`
- `sources/attachment_deferred/full_source_protocol/shards.jsonl`
- `sources/attachment_deferred/full_source_protocol/validation.json`
- `sources/attachment_deferred/full_source_protocol/commands.md`
- `sources/attachment_deferred/full_source_protocol/report.md`
- `bootstrap_ci/manifest.json`
- `bootstrap_ci/summary.json`
- `bootstrap_ci/summary.md`
- `sources/qwen_vl/adapter_contract.json`
- `sources/qwen_vl/input_schema.json`
- `sources/qwen_vl/input_schema_example.json`
- `sources/qwen_vl/model_candidates.json`
- `sources/qwen_vl/output_schema.json`
- `sources/qwen_vl/output_jsonl_contract.md`
- `sources/qwen_vl/prompt_templates.md`
- `sources/qwen_vl/prediction_schema_example.json`
- `sources/qwen_vl/validation/manifest.json`
- `sources/qwen_vl/validation/report.md`
- `sources/qwen_vl/tiny_pilot/input.jsonl`
- `sources/qwen_vl/tiny_pilot/manifest.json`
- `sources/qwen_vl/tiny_pilot/report.md`
- `sources/qwen_vl/runtime_plan/model_recommendation.json`
- `sources/qwen_vl/runtime_plan/report.md`
- `sources/qwen_vl/crops/records.jsonl`
- `sources/qwen_vl/crops/manifest.json`
- `sources/qwen_vl/crops/report.md`
- `sources/qwen_vl/full_source_input/manifest.json`
- `sources/qwen_vl/full_source_input/report.md`
- `sources/qwen_vl/full_source_crops/shards/qwen_full_source_shard_0000/manifest.json`
- `sources/qwen_vl/full_source_crops/shards/qwen_full_source_shard_0000/report.md`
- `sources/qwen_vl/full_source_crops/all/manifest.json`
- `sources/qwen_vl/full_source_crops/all/report.md`
- `sources/qwen_vl/full_source_inference_plan/manifest.json`
- `sources/qwen_vl/full_source_inference_plan/runner_contract.json`
- `sources/qwen_vl/full_source_inference_plan/shards.jsonl`
- `sources/qwen_vl/full_source_runtime/dry_runs/qwen_full_source_shard_0000.json`
- `manifest.lock.json`
- `report.md`

## Run

Use the commands in `commands.md`. Paper-facing outputs must be generated through Docker.

## Claim Boundary

Allowed now:

```text
Scoped geometry-consistency reliability-layer result across reproduced VL-SAT and Open3DSG within measured H001 families.
```

Still blocked:

```text
Broad open-vocabulary 3DSSG generation improvement claim beyond the measured H001-family closed-set/GT-object scope.
Adding relative_horizontal to the main claim before its separate validation track reaches the current H001 evidence standard.
Adding attachment_deferred to the main claim before its full-source scoring protocol, source metrics, controls, bootstrap CI, and audit reach the current H001 evidence standard. The completed G0-G5b artifacts are upgrade-readiness evidence, not current source metric evidence. Even after the remaining gates pass, main-claim promotion requires explicit final user confirmation.
```

Current Open3DSG blocker:

```text
No metric blocker remains. H001 eval feature cache is complete for the covered loadable scope: shard loop exit 0, 377/377 complete feature ids, 1131 .pt files, and feature_audit_h001_eval missing complete feature ids 0. The audit still records the known validation_missing_preprocessed:11 caveat. Source patch schema h001_open3dsg_source_patch_v12 aligns BLIP relationship image embedding dtype and switches BLIP generation to max_new_tokens. The v12 raw dump retry wrote 19162 rows to raw_dump/raw.jsonl and Docker open3dsg_raw_dump_identity reports raw_dump_identity_audit_ready with no blockers. Clean v14 streaming same-path resume then completed source-process provenance with exit 0, manifest status raw_dump_stream_complete, 377/377 completed batches, 19162 rows, dropped/invalid partial rows 0/0, and SHA256 matching raw_dump/raw.jsonl. Historical exit-137 attempts remain run records. Adapter export, geometry join, metric eval, failure rows, qualitative case inspection, paper caveats, and Table 6 regeneration are ready. Paper caveats freeze filtered train 3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered loadable scope 377/388 contexts, averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and residual calibration-risk wording.
```

Current Open3DSG metric/join blocker:

```text
none. Docker open3dsg_metric_eval status is ready with 496600 predictions, 7505 GT rows, 496600 geometry rows, and no blockers. Table 6 reads sources/open3dsg/metrics/metrics.json.
```

Current Open3DSG checkpoint-selection blocker:

```text
checkpoint selection is refreshed after the official non-averaged BLIP R1 retry. Docker `open3dsg_checkpoint_selection` status is `checkpoint_selection_ready_official_non_avg_blip`; selected checkpoint: `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`, sha256 `ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb`, chosen by train-dev `val/loss=0.5724539160728455` at step 13103 before selected-route H001 held-out raw dump/metrics/failure analysis/visual inspection. Route comparison is unfavorable to non-avg on train-dev loss for the historical 127-scan branch: best avg-BLIP checkpoint remains `0.32881081104278564`, so non-avg minus avg is `+0.24364310503005981`. Current paper-facing Open3DSG evidence uses the full-validation 548/548 recovery branch with explicit recovery-policy caveat; the historical avg-BLIP metrics/caveats stay local to the 127-scan branch.
```

Current Open3DSG raw-dump identity status:

```text
raw-dump identity audit is ready with H001 scope 127 scans / 388 contexts / 25,916 directed pairs. raw_dump/raw.jsonl has 19162 rows; adapter, geometry join, metric eval, and Table 6 all passed downstream. Clean v14 streaming raw-dump resume completed with exit 0 and produced a byte-identical row set to raw_dump/raw.jsonl, so source-process provenance is available. Paper-facing caveats are frozen under `paper_caveats/`. Optional covered-context reduction is now planned but not executed: retry the 11 missing H001 preprocess contexts, then rerun feature audit and the downstream raw-dump/metric chain only if coverage improves.
```

Current Open3DSG metric-scope policy:

```text
predicate-family mapping and denominator caveat are frozen; in-scope GT denominator is 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. relative_horizontal has 3,570 excluded GT rows and is tracked only as a separate expansion candidate. Its coordinate audit and bucket inspection are blocked for main-claim promotion: best scan-frame macro strict purity 0.7725, left/right 0.8005, front/behind 0.7445, inverse consistency 1.0, wrong-frame gap 0.1231, front/behind match:contradiction 2.9143, and ambiguity flags axis_margin_ambiguous 230 / conflicting_axis_dominates 430 / strong_projected_overlap 44. Table 6 requires the current policy before real Open3DSG metrics can be promoted.
attachment_deferred has 967 excluded GT rows and is tracked as the preferred future physical-relation upgrade, not current metric evidence. Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry run, G1c point/surface validation, G2 verifier-policy design, G3 calibration/counterfactual route, G4 GT policy smoke, G4b error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a pooled strict calibration fit, G5b bounded source scoring preflight, and G5c full-source protocol freeze are complete and freeze the candidate denominator, source rows, unsupported verification status, evidence-only output contract, point/surface-ready evidence rows, conservative 9-subtype policy, train/dev policy-decision readiness, error taxonomy, calibration-filter dispositions, visual sanity queue, strict calibration subset, pooled p_geom model, bounded source scoring contract, deterministic shards, source-specific covered denominators, metric conditions, and control order. Promotion still requires full-source scoring, VL-SAT/Open3DSG source metrics, controls, bootstrap CI, and audit before Table 6 can include it. Visual labels remain useful for a soft protocol, but the strict-only route is now frozen.
```

Current Open3DSG Table 6 hook:

```text
table builder reads sources/open3dsg/metrics/metrics.json and marks Open3DSG Table 6 ready with no blockers, scoped to measured H001 families. The regenerated Table 6 includes a caveat_note for averaged-BLIP, filtered train/dev, covered H001 377/388, exact-label denominator 2545, validation_missing_preprocessed:11, and residual calibration risk.
```
