# Qwen-VL Adapter Contract Report

Status: `full_source_inference_remaining_loop_running_non_metric`
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

The crop-rendering stage still ran no Qwen model load and no inference. Full
Qwen inference may now be scheduled shard-wise, but its outputs remain non-metric
until parser validation, adapter export, geometry join, metrics, controls,
bootstrap, and audit complete.

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
- remaining shard loop status: `running_non_metric`
- remaining shard loop tmux: `h001_qwen_vl_infer_remaining`
- remaining shard loop run id: `20260527_023111`
- remaining shard loop scope: `qwen_full_source_shard_0001` through `qwen_full_source_shard_0133`, 133 shards, 33,134 expected rows
- remaining shard loop command: `QWEN_VL_LOOP_RUN_ID=20260527_023111 QWEN_VL_LOOP_START_SUFFIX=0001 QWEN_VL_LOOP_END_SUFFIX=0133 bash experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_shard_loop.sh`
- remaining shard loop log: `logs/qwen_vl_full_source_infer_remaining_20260527_023111.log`
- remaining shard loop status TSV: `logs/qwen_vl_full_source_infer_remaining_20260527_023111.status.tsv`
- remaining shard loop exit file: `logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit`

The first inference shard is complete and contract-validated, but it is still
not paper metric evidence. The remaining shards are now running as a sequential
resumable background loop. The next dependent step is all-shard completion
verification and parser validation.
