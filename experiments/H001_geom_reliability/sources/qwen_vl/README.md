# Qwen-VL Semantic-Source Adapter

Status: `full_validation_downstream_metrics_ready_third_source_extension`
Created at: `2026-05-08T06:35:07+00:00`

## Role

Qwen-VL is the third semantic source / modern VLM extension for H001.
It is not a replacement for the Open3DSG reproduction anchor, not a replacement
for the VL-SAT controlled anchor, and not an end-to-end 3DSSG training result.

## Model Ladder

- recommended small modern main: `Qwen/Qwen3-VL-4B-Instruct`
- stable small fallback: `Qwen/Qwen2.5-VL-3B-Instruct`
- lowest-cost parser smoke: `Qwen/Qwen3-VL-2B-Instruct`
- optional quality follow-ups: `Qwen/Qwen3-VL-8B-Instruct`, `Qwen/Qwen2.5-VL-7B-Instruct`

## Contract Files

- `Dockerfile.qwen`: Docker runtime image for Qwen-VL cache/runtime smoke
- `compose.qwen.yaml`: Docker services for model download, cache verify, runtime preflight, and tiny inference smoke
- `adapter_contract.json`: model candidates, schemas, pilot plan, and claim boundary
- `input_schema.json`: frozen input JSON Schema
- `input_schema_example.json`: example input JSONL row
- `output_schema.json`: frozen output JSONL row JSON Schema
- `output_jsonl_contract.md`: human-readable output JSONL contract
- `model_candidates.json`: candidate model ladder including 2B/3B/4B options
- `prediction_schema_example.json`: example identity-preserving output row
- `prompt_templates.md`: semantic-only and diagnostic prompt templates
- `commands.qwen_vl.md`: Docker command entrypoint for this contract
- `report.md`: human-readable summary
- `validation/`: contract-only validator/parser skeleton outputs after running `qwen_vl_contract_validator`
- `tiny_pilot/`: non-held-out 30-row pilot input scope and validator outputs
- `runtime_plan/`: crop-rendering preflight and recommended model id/revision/local-dir
- `crops/`: pair-crop rendering records/manifest/report; crop images stay under ignored `local_dataset/qwen_vl_crops/`
- `model_cache/`: timestamped long-running model-cache job records
- `runtime_smoke/`: cache/preflight/tiny-inference smoke outputs after the relevant Docker services run
- `full_source_plan/`: frozen third-source promotion protocol before any full Qwen paper-metric run
- `full_source_input/`: full H001 directed-pair/family input universe, inferable input rows, missing-row policy, shard list, and contract validation
- `full_source_crops/`: full-source pair-crop render/preflight records; PNG crops stay under ignored `local_dataset/qwen_vl_crops/full_source/`
- `full_source_inference_plan/`: sharded inference runner contract, resume policy, per-shard command templates, and no-inference plan manifest
- `full_source_runtime/`: completed non-metric shard runtime root with manifests, predictions, raw responses, progress files, and reports
- `full_source_validation/`: all-shard aggregation and contract parser validation over the completed runtime outputs
- `adapter/`: H001 `h001_prediction_v1` prediction export and copied ground truth
- `geometry/`: H001 geometry join over Qwen predictions
- `metrics/`: recall/violation metrics and controls
- `bootstrap_ci/`: subgraph-bootstrap confidence intervals for Qwen-VL metrics
- `failure_rows/`: Qwen-VL failure-analysis rows generated against the fixed H001 taxonomy
- `failure_cases/`: deterministic qualitative failure-case queue and inspection summary
- `full_validation/`: full official validation migration branch; keeps
  input/crop/runtime/downstream artifacts separate from the historical
  127-scan `full_source_*` route

## Current Runtime State

- model-cache job: completed, exit code `0`
- log: `logs/qwen_vl_model_download_20260512_082830.log`
- exit file: `logs/qwen_vl_model_download_20260512_082830.exit`
- model id: `Qwen/Qwen3-VL-4B-Instruct`
- revision: `ebb281ec70b05090aa6165b016eac8ec08e71b17`
- local dir: `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`
- cache verification: `model_cache_ready`, 43 files, 8.277 GB, 3 weight/index files
- runtime preflight: `runtime_preflight_passed`
- runtime preflight log: `logs/qwen_vl_runtime_preflight_20260527_002150.log`
- tiny inference smoke: `tiny_inference_smoke_passed`
- tiny inference log: `logs/qwen_vl_tiny_inference_smoke_20260527_002330.log`
- tiny inference outputs: 3 attempted rows, 3 output rows, parser status counts `{'parsed': 3}`
- runtime contract validation: `validator_parser_skeleton_ready_no_model_runtime`
- validation log: `logs/qwen_vl_tiny_inference_contract_validate_20260527_002427.log`
- compatibility patch: `run_qwen_vl_runtime_smoke.py` avoids Python 3.10-only `zip(strict=True)` so the runtime image works on the Python 3.9 Qwen/Open3DSG base image
- full-source promotion plan: `full_source_promotion_plan_frozen_no_metric_run`
- full-source plan log: `logs/qwen_vl_full_source_plan_20260527_003349.log`
- full-source plan scope: 127 scans / 388 contexts / 25,916 directed pairs; max all-pairs x family query rows 77,748; in-scope GT denominator 2,545
- full-source input audit: `full_source_input_ready_with_missing_rows_no_inference`
- full-source input log: `logs/qwen_vl_full_source_input_20260527_005933.log`
- full-source input validation log: `logs/qwen_vl_full_source_input_validate_20260527_010011.log`
- full-source input counts: 77,748 universe query rows, 33,384 inferable input rows, 44,364 missing rows, 134 shards
- full-source input validation: 33,384 input rows, 0 input errors, 0 output errors, 0 warnings
- full-source crop shard smoke: `qwen_full_source_shard_0000`, 250 input rows, 84 unique pair crops, preflight 84/84, 0 errors
- full-source crop shard logs: `logs/qwen_vl_full_source_crop_render_shard0000_20260527_012801.log`, `logs/qwen_vl_full_source_crop_preflight_shard0000_20260527_012813.log`
- full-source crop render all: completed with exit `0`, log `logs/qwen_vl_full_source_crop_render_all_20260527_012856.log`, exit file `logs/qwen_vl_full_source_crop_render_all_20260527_012856.exit`
- full-source crop all-scope preflight: `full_source_crop_preflight_ready_no_inference`, 33,384 input rows, 11,128 unique pair crops, 11,128 verified crops, 0 errors
- full-source crop all-scope preflight log: `logs/qwen_vl_full_source_crop_preflight_all_20260527_013235.log`
- full-source crop all-scope artifact: `full_source_crops/all/{records.jsonl,manifest.json,report.md}`
- full-source inference runner plan: `full_source_inference_runner_frozen_no_inference`
- full-source inference runner plan log: `logs/qwen_vl_full_source_inference_plan_20260527_020314.log`
- full-source inference runner plan artifact: `full_source_inference_plan/{manifest.json,runner_contract.json,shards.jsonl,commands.md,report.md}`
- full-source inference shard dry-run: `qwen_full_source_shard_0000`, 250 rows, 84 unique pair crops, 0 blockers
- full-source inference shard dry-run log: `logs/qwen_vl_full_source_infer_dry_run_shard0000_20260527_020324.log`
- full-source inference shard launch: tmux `h001_qwen_vl_infer_qwen_full_source_shard_0000`
- full-source inference shard log: `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.log`
- full-source inference shard exit file: `logs/qwen_vl_full_source_infer_qwen_full_source_shard_0000_20260527_021706.exit`
- full-source inference shard status: `full_source_inference_shard_complete`
- full-source inference shard counts: 250 predictions, 250 raw responses, 250 completed rows, parser status `parsed:250`
- full-source inference shard validation: `validator_parser_skeleton_ready_no_model_runtime`, 250 parsed rows, 0 input errors, 0 output errors, 0 warnings
- full-source inference shard validation log: `logs/qwen_vl_full_source_shard0000_contract_validate_20260527_022224.log`
- previous remaining full-source shard loop: tmux `h001_qwen_vl_infer_remaining`, run id `20260527_023111`
- previous remaining full-source shard loop result: stopped with exit `1` at `qwen_full_source_shard_0014` because the GPU guard observed utilization 36% against the 35% threshold; shards `0000` through `0013` are complete, 3,500 rows are written
- resumed remaining full-source shard loop: tmux `h001_qwen_vl_infer_remaining_resume_20260611_000531`, run id `20260611_000531`, status `complete_non_metric`
- resumed remaining full-source shard loop scope: `qwen_full_source_shard_0014` through `qwen_full_source_shard_0133`, 120 shards, 29,884 expected rows
- resumed remaining full-source shard loop command: `QWEN_VL_LOOP_RUN_ID=20260611_000531 QWEN_VL_LOOP_START_SUFFIX=0014 QWEN_VL_LOOP_END_SUFFIX=0133 bash experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_shard_loop.sh`
- resumed remaining full-source shard loop log: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.log`
- resumed remaining full-source shard loop status TSV: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.status.tsv`
- resumed remaining full-source shard loop exit file: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.exit`, value `0`
- resumed remaining full-source shard loop completion: final shard `qwen_full_source_shard_0133` finished at `2026-06-11T06:47:32+09:00` with exit `0`
- full-source runtime file counts: 134/134 manifests, 134/134 prediction JSONL files, 134/134 raw-response JSONL files, 134/134 completed-progress JSONL files, 134/134 JSON reports, and 134/134 Markdown reports
- full-source runtime row counts: 33,384 prediction rows, 33,384 raw-response rows, and 33,384 completed-progress rows
- full-source parser status counts: `parsed:33383`, `parsed_with_warning:1`
- parser warning row: `qwen_vl:h001_validation_hardened:4a9a43d4-7736-2874-87a6-0c3089281af8_2:62:44:support_contact`; warning is a duplicate `lying on` predicate in the model response, with one deduplicated top prediction retained
- tmux status: no active Qwen inference session remains after completion
- full-source aggregation: `qwen_vl_full_source_aggregate_ready`, 33,384 raw-response rows, 33,384 runtime prediction rows, 33,384 completed rows
- all-shard parser validation: 33,384 input rows, 33,384 parsed rows, 0 input errors, 0 output errors, 0 warnings
- adapter export: `qwen_vl_adapter_export_ready`, 25,262 exported predictions, 23,084 in-scope predictions, 7,505 ground-truth rows, 2,545 target-family GT rows, 1,845 target-family GT rows with Qwen input-pair coverage, 932 exact-label GT keys hit by Qwen predictions
- canonicalization policy: `next to`/`near` -> `close by`, `above` -> `higher than`, `under` -> `lower than`; `far from` and `part of` remain `unsupported_first_pass`
- geometry join: `ready`, 25,262 preserved verification rows, 23,084 geometry-available/scored H001-family rows, 2,178 unsupported-family rows, status counts `satisfied:14548`, `uncertain:5599`, `unsupported:2178`, `violated:2937`
- metric eval: `ready`; semantic_only R@50/R@100 `0.2684/0.3580`, V@50/@100 `0.1239/0.1260`; probabilistic_recalibrated `0.3092/0.3654`, V `0.0787/0.1167`; rule_verified_point_subtype `0.2904/0.3631`, V `0.0/0.0`; family_specific control `0.3308/0.3654`, V `0.0499/0.1106`
- bootstrap CI: `ready`, 1,000 subgraph resamples; probabilistic_recalibrated vs semantic_only delta at @50 is R `+0.0409` with 95% CI `[+0.0262,+0.0555]` and V `-0.0452` with 95% CI `[-0.0513,-0.0396]`
- failure rows: `failure_analysis_real_ready`, 22,787 diagnostic rows, 2,843 visual-audit queue rows, validation errors 0
- qualitative inspection: `qualitative_case_inspection_ready`, 36 deterministic cases, 27 demoted by geometry-aware reranking, 9 promoted or retained, 7 rule-violated cases with `p_geom_valid > 0.9`

## Full Official Validation Migration

- status: `full_validation_qwen_downstream_metrics_ready_third_source_extension`
- branch root: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/`
- scope: 157 scans / 548 contexts / 36,808 directed pairs / 110,424 all-pairs x family query rows / 3,972 H001-family GT rows
- input audit: 46,506 inferable input rows, 63,918 missing query rows, 187 shards
- input validation: `validator_parser_skeleton_ready_no_model_runtime`
- crop render/preflight: 15,502 unique pair crops verified, 0 errors
- inference: completed; tmux `h001_qwen_fullval_infer_loop` is no longer active
- inference run id: `20260611_141736`
- inference log: `logs/h001_qwen_fullval_infer_loop_20260611_141736.log`
- inference status TSV: `logs/qwen_vl_full_validation_infer_20260611_141736.status.tsv`
- inference exit status: outer exit `0`, loop exit `0`
- completed shards/rows: 187/187 shards, 46,506/46,506 inference rows
- downstream run id: `20260612_031601`
- downstream status TSV: `logs/h001_qwen_fullval_downstream_20260612_031601.status.tsv`
- downstream tail rerun status TSV: `logs/h001_qwen_fullval_failure_tail_20260612_031805.status.tsv`
- contract validation: 46,506 parsed rows, 0 input errors, 0 output errors, 0 warnings
- adapter export: 35,131 predictions, 32,236 in-scope predictions, 3,972 H001-family GT rows, 1,453 exact-label GT keys hit by Qwen predictions
- metrics/controls/bootstrap: `ready`
- failure rows: `failure_analysis_real_ready`, 31,881 metric-eligible diagnostic rows, 3,939 visual-audit queue rows
- deterministic qualitative cases: `qualitative_case_inspection_ready`, 36 cases, 27 demoted by geometry-aware reranking, 9 promoted or retained

This branch is the only Qwen route that can be considered for paper-facing
full-validation evidence. The completed historical 127-scan route remains
extension/sanity evidence unless explicitly labeled otherwise.

### Full-Validation Metrics

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.2815 | 0.3600 | 0.1226 | 0.1246 |
| `probabilistic_recalibrated` | 0.3215 | 0.3653 | 0.0795 | 0.1166 |
| `rule_verified_point_subtype` | 0.3009 | 0.3630 | 0.0000 | 0.0000 |
| `control_family_specific_p_geom_valid` | 0.3379 | 0.3653 | 0.0510 | 0.1113 |

Bootstrap summary: probabilistic recalibration improves R@50 by `+4.00 pp` and
reduces V@50 by `-4.31 pp`; at @100 the gains are smaller (`+0.53 pp` recall,
`-0.80 pp` violation). Family-specific `p_geom_valid` gives the strongest
top-50 tradeoff (`+5.64 pp` R@50, `-7.16 pp` V@50).

## Next Gate

No additional Qwen downstream experiment is required for the current AAAI claim.
The paper-claim decision is fixed on 2026-06-12 KST: keep Qwen as
appendix/extension evidence showing that the H001 geometry-consistency failure
mechanism also appears for a modern crop-based VLM source. Do not replace
VL-SAT or Open3DSG with Qwen in the current main source-result table.
