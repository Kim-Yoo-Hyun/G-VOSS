# Qwen-VL Semantic-Source Adapter

Status: `full_validation_extension_downstream_ready_appendix_only`
Created at: `2026-05-08T06:35:07+00:00`
Last updated: 2026-06-14 KST

## Current State, 2026-06-14 KST

Qwen-VL is now a completed third semantic source / modern VLM extension for
the full official validation route. It is not a replacement for the VL-SAT
controlled anchor or the Open3DSG main open-vocabulary relation-source case
study.

Full-validation row artifacts live under:

```text
experiments/H001_geom_reliability/sources/qwen_vl/full_validation/
```

Current scope and outputs:

- 157 scans / 548 contexts
- 110,424 query rows
- 46,506 inferable input rows and 63,918 missing query rows
- 187 runtime shards
- 35,131 exported predictions
- 32,236 in-scope predictions
- 3,972 H001-family GT rows
- 31,881 failure rows
- 36 deterministic qualitative cases

Key diagnostic metrics:

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.2815 | 0.3600 | 0.1226 | 0.1246 |
| `probabilistic_recalibrated` | 0.3215 | 0.3653 | 0.0795 | 0.1166 |
| `rule_verified_point_subtype` | 0.3009 | 0.3630 | 0.0000 | 0.0000 |
| `family_specific` | 0.3379 | 0.3653 | 0.0510 | 0.1113 |

Paper boundary: keep Qwen-VL as appendix/extension evidence unless the main
claim is explicitly widened. The older `full_source_*` sections below describe
the historical 127-scan runtime plan/resume path and should not be read as the
current active blocker.

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
- `full_source_plan/`: historical 127-scan third-source promotion protocol before the later full-validation extension route
- `full_source_input/`: full H001 directed-pair/family input universe, inferable input rows, missing-row policy, shard list, and contract validation
- `full_source_crops/`: full-source pair-crop render/preflight records; PNG crops stay under ignored `local_dataset/qwen_vl_crops/full_source/`
- `full_source_inference_plan/`: sharded inference runner contract, resume policy, per-shard command templates, and no-inference plan manifest
- `full_source_runtime/`: future shard runtime root; current content is dry-run metadata only

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
- historical resumed remaining full-source shard loop: tmux `h001_qwen_vl_infer_remaining_resume_20260611_000531`, run id `20260611_000531`; superseded by the full-validation extension state summarized above
- resumed remaining full-source shard loop scope: `qwen_full_source_shard_0014` through `qwen_full_source_shard_0133`, 120 shards, 29,884 expected rows
- resumed remaining full-source shard loop command: `QWEN_VL_LOOP_RUN_ID=20260611_000531 QWEN_VL_LOOP_START_SUFFIX=0014 QWEN_VL_LOOP_END_SUFFIX=0133 bash src/geocalib/run_qwen_vl_full_source_shard_loop.sh`
- resumed remaining full-source shard loop log: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.log`
- resumed remaining full-source shard loop status TSV: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.status.tsv`
- resumed remaining full-source shard loop exit file: `logs/qwen_vl_full_source_infer_remaining_20260611_000531.exit` when the loop finishes
- resumed progress check: shard `0014` started at `2026-06-11T00:05:31+09:00`, completed with exit `0` at `2026-06-11T00:08:58+09:00`, and shard `0015` started immediately afterward
- resumed shard `0014` output: manifest `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/manifests/qwen_full_source_shard_0014.json`, status `full_source_inference_shard_complete`, 250 selected rows, 84 unique pair crops, family counts proximity/support/relative-vertical `83/83/84`

## Next Gate

No active Qwen-VL shard loop is the current paper blocker. Before reporting
Qwen-VL beyond appendix/extension text, verify that the full-validation metric
summary, bootstrap summary, failure rows, qualitative cases, and any package
manifests are present in the release artifact set. Promotion into the main
claim requires an explicit user decision.
