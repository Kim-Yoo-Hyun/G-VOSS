# Qwen-VL Adapter Contract Report

Status: `full_validation_downstream_metrics_ready_third_source_extension`
Created at: `2026-05-08T06:35:07+00:00`

## Decision

Use Qwen-VL as the third semantic source / modern VLM extension after recording the Open3DSG reproduction anchor.
Start with small models: `Qwen3-VL-4B-Instruct` as the recommended modern target, `Qwen2.5-VL-3B-Instruct` as stable fallback, and `Qwen3-VL-2B-Instruct` for lowest-cost parser smoke.

## Claim Boundary

- allowed: modern VLM semantic-source reliability with H001 geometry reranking
- not allowed: end-to-end 3DSSG generation claim
- not allowed: replacement of Open3DSG reproduction evidence
- not allowed: replacement of the VL-SAT controlled anchor

## Acceptance Gates

- frozen `input_schema.json` and `output_schema.json` before model downloads or inference
- contract-only validator/parser skeleton before model downloads or inference
- non-held-out tiny pilot scope before model downloads or inference
- fixed model id and revision/local-dir before held-out metrics
- frozen prompt templates and parser
- identity-preserving prediction JSONL
- semantic-only prompt must not receive verifier labels or geometry scores
- Docker-generated outputs only for paper-result promotion

## Runtime Smoke Result

- cache verification: `model_cache_ready`
- runtime preflight: `runtime_preflight_passed`
- tiny inference smoke: `tiny_inference_smoke_passed`
- attempted rows: `3`
- output rows: `3`
- parser status counts: `{'parsed': 3}`
- contract validation over runtime raw responses: `validator_parser_skeleton_ready_no_model_runtime`
- logs:
  - `logs/qwen_vl_runtime_preflight_20260527_002150.log`
  - `logs/qwen_vl_tiny_inference_smoke_20260527_002330.log`
  - `logs/qwen_vl_tiny_inference_contract_validate_20260527_002427.log`

## Claim Boundary

This smoke result proves the locked Qwen3-VL-4B cache, processor/model load,
prompt route, strict JSON parse, and H001 output contract are executable in
Docker. It is not a paper metric and does not replace the Open3DSG reproduction
anchor or the VL-SAT controlled anchor.

## Full-Source Promotion Plan

- status: `full_source_promotion_plan_frozen_no_metric_run`
- plan artifact: `full_source_plan/{manifest.json,protocol.json,commands.md,report.md}`
- log: `logs/qwen_vl_full_source_plan_20260527_003349.log`
- role: third semantic source / modern VLM extension
- frozen H001 identity scope: 127 scans, 388 contexts, 25,916 directed pairs
- maximum all-pairs x family query rows: 77,748
- in-scope GT denominator: 2,545 rows across support_contact/proximity/relative_vertical

Promotion requires a complete directed-pair candidate universe, not only
GT-positive rows. Qwen can enter paper tables only after Docker input audit,
sharded inference, parser validation, adapter export, geometry join, R@K /
Violation@K metrics, controls, bootstrap CI, and qualitative/failure audit.

## Full-Source Input Audit

- status: `full_source_input_ready_with_missing_rows_no_inference`
- input artifact: `full_source_input/{manifest.json,coverage.json,report.md}`
- log: `logs/qwen_vl_full_source_input_20260527_005933.log`
- validation log: `logs/qwen_vl_full_source_input_validate_20260527_010011.log`
- universe query rows: 77,748
- inferable input rows: 33,384
- missing rows: 44,364
- shard count: 134 with shard size 250
- contract validation: 33,384 input rows, 0 input errors, 0 output errors, 0 warnings

Missing rows are retained in `missing.jsonl` with reasons and must be reported
as a Qwen-specific denominator caveat. The next gate is crop rendering or
render-on-demand shard preflight for all inferable rows, not full metric
promotion.

## Full-Source Crop Rendering

- shard smoke status: `full_source_crop_preflight_ready_no_inference`
- shard id: `qwen_full_source_shard_0000`
- shard smoke counts: 250 input rows, 84 unique pair crops, 84 verified existing crops, 0 errors
- shard smoke artifact: `full_source_crops/shards/qwen_full_source_shard_0000/{records.jsonl,manifest.json,report.md}`
- shard logs: `logs/qwen_vl_full_source_crop_render_shard0000_20260527_012801.log`, `logs/qwen_vl_full_source_crop_preflight_shard0000_20260527_012813.log`
- full render status: `completed_exit_0`
- full render log: `logs/qwen_vl_full_source_crop_render_all_20260527_012856.log`
- full render exit file: `logs/qwen_vl_full_source_crop_render_all_20260527_012856.exit`
- all-scope preflight status: `full_source_crop_preflight_ready_no_inference`
- all-scope preflight counts: 33,384 input rows, 11,128 unique pair crops, 11,128 verified crops, 0 errors
- all-scope preflight log: `logs/qwen_vl_full_source_crop_preflight_all_20260527_013235.log`
- all-scope preflight artifact: `full_source_crops/all/{records.jsonl,manifest.json,report.md}`

The crop-rendering stage itself ran no Qwen model load and no inference. The
later full-source inference and downstream metric/audit stages are recorded
below.

## Full-Source Inference Runner

- status: `full_source_inference_runner_frozen_no_inference`
- plan artifact: `full_source_inference_plan/{manifest.json,runner_contract.json,shards.jsonl,commands.md,report.md}`
- plan log: `logs/qwen_vl_full_source_inference_plan_20260527_020314.log`
- planned rows: 33,384
- planned shards: 134
- runner services: `qwen_vl_full_source_infer_dry_run`, `qwen_vl_full_source_infer_shard`
- resume key: `record_id`
- dry-run shard: `qwen_full_source_shard_0000`, 250 rows, 84 unique pair crops, 0 blockers
- dry-run log: `logs/qwen_vl_full_source_infer_dry_run_shard0000_20260527_020324.log`
- shard 0000 launch status: `full_source_inference_shard_complete`
- shard 0000 tmux: `h001_qwen_vl_infer_qwen_full_source_shard_0000`
- shard 0000 log: `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.log`
- shard 0000 exit file: `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.exit`
- shard 0000 counts: 250 predictions, 250 raw responses, 250 completed rows, parser status `parsed:250`
- shard 0000 validation: `validator_parser_skeleton_ready_no_model_runtime`, 250 parsed rows, 0 input errors, 0 output errors, 0 warnings
- shard 0000 validation log: `logs/qwen_vl_full_source_shard0000_contract_validate_20260527_022224.log`
- previous remaining shard loop run id: `20260527_023111`, stopped at `qwen_full_source_shard_0014` because of GPU utilization guard; shards 0000-0013 completed with 3,500 rows
- resumed remaining shard loop status: `complete_non_metric`
- resumed remaining shard loop tmux: `h001_qwen_vl_infer_remaining_resume_20260611_000531`
- resumed remaining shard loop run id: `20260611_000531`
- resumed remaining shard loop scope: `qwen_full_source_shard_0014` through `qwen_full_source_shard_0133`, 120 shards, 29,884 expected rows
- resumed remaining shard loop command: `QWEN_VL_LOOP_RUN_ID=20260611_000531 QWEN_VL_LOOP_START_SUFFIX=0014 QWEN_VL_LOOP_END_SUFFIX=0133 bash experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_shard_loop.sh`
- resumed remaining shard loop log: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.log`
- resumed remaining shard loop status TSV: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.status.tsv`
- resumed remaining shard loop exit file: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.exit`, value `0`
- final shard: `qwen_full_source_shard_0133`, finished `2026-06-11T06:47:32+09:00`, exit `0`
- full-source runtime file counts: 134/134 manifests, prediction files, raw-response files, completed-progress files, JSON reports, and Markdown reports
- full-source runtime row counts: 33,384 prediction rows, 33,384 raw-response rows, and 33,384 completed-progress rows
- parser status counts over prediction rows: `parsed:33383`, `parsed_with_warning:1`
- parser warning row: `qwen_vl:h001_validation_hardened:4a9a43d4-7736-2874-87a6-0c3089281af8_2:62:44:support_contact`; the model returned duplicate `lying on` predicates and the parser retained one deduplicated top prediction

## Full-Source Downstream Validation And Metrics

This section records the historical 127-scan inferable-pair route. It remains
useful as extension/sanity evidence, but the paper-facing Qwen route is now the
full official validation branch recorded below.

- aggregation status: `qwen_vl_full_source_aggregate_ready`
- contract validation: 33,384 input rows, 33,384 parsed rows, 0 input errors, 0 output errors, 0 warnings
- adapter export: `qwen_vl_adapter_export_ready`, 25,262 exported predictions, 23,084 in-scope predictions, 2,545 target-family GT rows, 1,845 target-family GT rows with Qwen input-pair coverage, 932 exact-label GT keys hit by Qwen predictions
- geometry join: `ready`, 25,262 preserved rows, 23,084 geometry-available/scored H001-family rows, 2,178 unsupported-family rows
- verification status counts: `satisfied:14548`, `uncertain:5599`, `unsupported:2178`, `violated:2937`
- semantic_only: R@50/R@100 `0.2684/0.3580`, Violation@50/@100 `0.1239/0.1260`
- probabilistic_recalibrated: R@50/R@100 `0.3092/0.3654`, Violation@50/@100 `0.0787/0.1167`
- rule_verified_point_subtype: R@50/R@100 `0.2904/0.3631`, Violation@50/@100 `0.0/0.0`
- control_family_specific_p_geom_valid: R@50/R@100 `0.3308/0.3654`, Violation@50/@100 `0.0499/0.1106`
- bootstrap CI: `ready`, 1,000 subgraph resamples; probabilistic_recalibrated vs semantic_only at @50 gives recall delta `+0.0409` with 95% CI `[+0.0262,+0.0555]` and violation delta `-0.0452` with 95% CI `[-0.0513,-0.0396]`
- failure rows: `failure_analysis_real_ready`, 22,787 diagnostic rows, 2,843 visual-audit queue rows, validation errors 0
- qualitative inspection: `qualitative_case_inspection_ready`, 36 deterministic cases, 27 demoted by geometry-aware reranking, 9 promoted or retained, 7 rule-violated cases with `p_geom_valid > 0.9`

## Full Official Validation Downstream

- branch root: `full_validation/`
- status: `full_validation_qwen_downstream_metrics_ready_third_source_extension`
- scope: 157 scans, 548 contexts, 36,808 directed pairs, 110,424 all-pairs x family query rows, 3,972 H001-family GT rows
- input rows: 46,506 inferable rows and 63,918 explicit missing query rows
- crop preflight: 15,502 unique pair crops verified, 0 errors
- inference: 187/187 shards, 46,506/46,506 prediction/raw/completed rows, exit `0`
- contract validation: 46,506 input rows, 46,506 parsed rows, 0 input errors, 0 output errors, 0 warnings
- adapter export: 35,131 predictions, 32,236 in-scope predictions, 1,453 exact-label GT keys hit by Qwen predictions
- geometry join / metrics / controls / bootstrap CI: `ready`
- failure rows: `failure_analysis_real_ready`, 31,881 diagnostic rows, 3,939 visual-audit queue rows
- qualitative inspection: `qualitative_case_inspection_ready`, 36 deterministic cases, 27 demoted by geometry-aware reranking, 9 promoted or retained, 6 rule-violated cases with `p_geom_valid > 0.9`

Key metrics:

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.2815 | 0.3600 | 0.1226 | 0.1246 |
| `probabilistic_recalibrated` | 0.3215 | 0.3653 | 0.0795 | 0.1166 |
| `rule_verified_point_subtype` | 0.3009 | 0.3630 | 0.0000 | 0.0000 |
| `control_family_specific_p_geom_valid` | 0.3379 | 0.3653 | 0.0510 | 0.1113 |

Bootstrap CI: probabilistic recalibration vs semantic-only gives @50 recall
delta `+4.00 pp` and violation delta `-4.31 pp`; at @100 it gives recall delta
`+0.53 pp` and violation delta `-0.80 pp`. Family-specific `p_geom_valid`
gives the strongest @50 tradeoff with recall delta `+5.64 pp` and violation
delta `-7.16 pp`.

## Downstream Claim Boundary

Qwen-VL can now be used as third-source modern-VLM extension evidence if the
paper needs it, because it has parser validation, adapter export, geometry join,
metrics, controls, bootstrap CI, and diagnostic audit artifacts. It should not
replace Open3DSG or VL-SAT and should not be promoted into the main AAAI claim
without an explicit decision, because Qwen remains a crop-based VLM semantic
source with much weaker recall than VL-SAT/Open3DSG and still has explicit
full-validation missing-query denominator caveats. Its strongest paper role is
to show that the H001 reliability framework is source-agnostic enough to expose
the same semantic-plausibility versus physical-consistency failure pattern in a
modern VLM source.
