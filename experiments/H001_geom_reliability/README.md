# H001 Geometry Reliability Experiment

Last updated: 2026-05-28

This is the first paper-body experiment workflow for H001. It is Docker-based by rule.

## Scope

Current executable sources:

- `VL-SAT` / `vlsat_closed_set`
- `Open3DSG` / `open3dsg_ov`

Selected top-tier expansion:

- Open3DSG second-source adapter result after Dockerized checkpoint reproduction; checkpoint plan, `training_repro` metadata/split staging, full payload staging, train/validation views, explicit train/validation preprocess filtering, official BLIP TopK5/scales3 feature dump, Docker feature audit, avg-BLIP checkpoint reproduction, checkpoint selection, eval preflight, H001 held-out eval feature-cache generation, raw-dump identity checklist, adapter export, geometry join, metric eval, predicate-family/denominator metric-scope policy, pre-metric failure-analysis schema, synthetic failure row-generator smoke, real failure-analysis rows, qualitative case inspection, paper caveat wording, Table 6 hook, and subgraph bootstrap CI are ready.
- `relative_horizontal` is now a separate scope-expansion validation track under `sources/relative_horizontal/`. The no-training/no-inference Docker scope audit is ready, with 3,570 candidate GT rows and source rows for VL-SAT / Open3DSG, but current verification status remains unsupported. The Docker coordinate audit and bucket inspection are also ready and currently blocked: best scan-frame macro strict purity is 0.7725, `front`/`behind` strict purity is 0.7445, inverse consistency is 1.0, wrong-frame gap is 0.1231, and `front`/`behind` ambiguity buckets remain substantial. Recommendation is `do_not_promote_relative_horizontal_to_main_claim`. Current AAAI-path decision is to freeze this as appendix/limitation evidence and not run expanded-family metrics. This does not change the current main paper claim. It can only be promoted after coordinate-frame semantics, denominator audit, verifier policy, calibration, controls, source metrics, bootstrap CI, and failure/audit evidence reach the same standard as the current H001 families.
- `attachment_deferred` is now the preferred future relation-family upgrade under `sources/attachment_deferred/`, not current metric evidence. Docker G0 scope/schema audit and G1 extractor contract are complete with status `attachment_deferred_extractor_contract_ready_no_extraction`: it adds 967 GT rows (`attached to` 808, `hanging on` 126, `connected to` 33), with candidate source rows for VL-SAT 77,748 and Open3DSG 57,300, and current verification status `unsupported` for both sources. It is a better conceptual fit than relative-horizontal for H001's physical-consistency mechanism, but the next gate is a schema-validated G1b evidence-only dry run for surface type, local point contact, surface normals, gravity/hanging, contradictory support cues, and object-affordance-as-context before any verifier/calibration or source metrics.
- Qwen-VL third semantic source / modern VLM extension contract is ready under `sources/qwen_vl/`; recommended small model ladder is Qwen3-VL-4B first, Qwen2.5-VL-3B stable fallback, and Qwen3-VL-2B parser-smoke candidate. Frozen input JSON Schema, output JSONL contract, contract-only validator/parser skeleton, non-held-out tiny pilot scope, runtime model-lock plan, tiny-pilot pair-crop rendering path, model-cache verification, runtime preflight, 3-row tiny inference smoke, runtime raw-response validation, full-source promotion plan, full-source input audit, full-source crop preflight, and full-source inference runner plan are recorded. Current full-source input audit has 77,748 universe rows, 33,384 inferable input rows, 44,364 missing rows, and 134 shards. All-scope crop preflight passed for 33,384 input rows / 11,128 unique pair crops / 0 errors. Runner plan freezes 134 shard commands/resume policy; shards 0000-0013 are complete with 3,500 parsed rows, and run id `20260527_023111` stopped at shard 0014 because the GPU guard observed utilization 36% against the 35% threshold. This is not a replacement for VL-SAT or Open3DSG evidence, and no full Qwen paper-metric evaluation has run.

Current method framing:

```text
calibrated geometry-consistency evaluation and re-ranking framework
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
Adding attachment_deferred to the main claim before its separate evidence extractor dry run, verifier/calibration contract, source metrics, controls, bootstrap CI, and audit reach the current H001 evidence standard. The completed G0 scope/schema audit and G1 extractor contract are not metric evidence.
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
checkpoint selection is ready for the explicitly labeled averaged-BLIP variant. Selected checkpoint: epoch=13-step=13104.ckpt by train-dev val/loss 0.32881081104278564 at step 13103, before H001 held-out raw dump/metrics/failure analysis/visual inspection. Exact non-averaged BLIP route remains OOM-blocked and must be reported as a limitation.
```

Current Open3DSG raw-dump identity status:

```text
raw-dump identity audit is ready with H001 scope 127 scans / 388 contexts / 25,916 directed pairs. raw_dump/raw.jsonl has 19162 rows; adapter, geometry join, metric eval, and Table 6 all passed downstream. Clean v14 streaming raw-dump resume completed with exit 0 and produced a byte-identical row set to raw_dump/raw.jsonl, so source-process provenance is available. Paper-facing caveats are frozen under `paper_caveats/`.
```

Current Open3DSG metric-scope policy:

```text
predicate-family mapping and denominator caveat are frozen; in-scope GT denominator is 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. relative_horizontal has 3,570 excluded GT rows and is tracked only as a separate expansion candidate. Its coordinate audit and bucket inspection are blocked for main-claim promotion: best scan-frame macro strict purity 0.7725, left/right 0.8005, front/behind 0.7445, inverse consistency 1.0, wrong-frame gap 0.1231, front/behind match:contradiction 2.9143, and ambiguity flags axis_margin_ambiguous 230 / conflicting_axis_dominates 430 / strong_projected_overlap 44. Table 6 requires the current policy before real Open3DSG metrics can be promoted.
attachment_deferred has 967 excluded GT rows and is tracked as the preferred future physical-relation upgrade, not current metric evidence. Docker G0 scope/schema audit and G1 extractor contract are complete and freeze the candidate denominator, source rows, unsupported verification status, and evidence-only output contract. Promotion still requires a G1b attachment evidence extractor dry run and full H001 validation path before Table 6 can include it.
```

Current Open3DSG Table 6 hook:

```text
table builder reads sources/open3dsg/metrics/metrics.json and marks Open3DSG Table 6 ready with no blockers, scoped to measured H001 families. The regenerated Table 6 includes a caveat_note for averaged-BLIP, filtered train/dev, covered H001 377/388, exact-label denominator 2545, validation_missing_preprocessed:11, and residual calibration risk.
```
