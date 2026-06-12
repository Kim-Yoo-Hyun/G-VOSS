# Qwen-VL Full Official Validation

Status: `full_validation_qwen_downstream_metrics_ready_third_source_extension`
Last updated: `2026-06-12 KST`

This branch migrates Qwen-VL from the historical 127-scan inferable-pair
extension route to the paper-facing full official `3DSSG_subset` validation
scope. It does not overwrite the historical `sources/qwen_vl/full_source_*`
artifacts.

## Scope

- official validation scans: `157`
- official validation contexts: `548`
- directed object pairs: `36,808`
- target families: `support_contact`, `proximity`, `relative_vertical`
- all-pairs x family query universe: `110,424`
- H001-family GT denominator: `3,972`

## Current State

- input audit: `full_source_input_ready_with_missing_rows_no_inference`
- input rows eligible for Qwen inference: `46,506`
- missing query rows retained in `missing.jsonl`: `63,918`
- shard count: `187` at shard size `250`
- input contract validation: `validator_parser_skeleton_ready_no_model_runtime`
- crop render: completed with exit `0`
- crop render log: `logs/h001_qwen_fullval_crop_render_20260611_141248.log`
- crop render exit file: `logs/h001_qwen_fullval_crop_render_20260611_141248.exit`
- crop preflight: `full_source_crop_preflight_ready_no_inference`, 15,502
  verified unique pair crops, 0 errors
- inference loop: completed; tmux session `h001_qwen_fullval_infer_loop` is no
  longer active
- inference run id: `20260611_141736`
- inference log: `logs/h001_qwen_fullval_infer_loop_20260611_141736.log`
- inference status TSV: `logs/qwen_vl_full_validation_infer_20260611_141736.status.tsv`
- inference exit file: `logs/h001_qwen_fullval_infer_loop_20260611_141736.exit`
- inference exit status: outer exit `0`, loop exit `0`
- completed shards: `187/187`
- completed inference rows: `46,506/46,506`
- downstream run id: `20260612_031601`
- downstream tmux: `h001_qwen_fullval_downstream_20260612_031601`
- downstream status TSV: `logs/h001_qwen_fullval_downstream_20260612_031601.status.tsv`
- downstream exit file: `logs/h001_qwen_fullval_downstream_20260612_031601.exit`
- downstream status: aggregate, contract validation, adapter export, geometry
  join, metrics, and bootstrap CI completed; the first failure-row generation
  run exposed a schema enum mismatch.
- schema fix: `qwen_vl_full_validation_failure_generator` now uses the locked
  record type `qwen_vl_failure_analysis`; full-validation identity is carried by
  `split_name`, `source_name`, and `analysis_prefix`.
- failure-tail rerun id: `20260612_031805`
- failure-tail status TSV: `logs/h001_qwen_fullval_failure_tail_20260612_031805.status.tsv`
- failure-tail status: failure rows, deterministic case sampler, and case
  inspection completed with exit `0`.

Missing rows are Qwen-specific coverage caveats caused by unavailable
object-view metadata or missing shared subject/object pair views. They are
retained as explicit denominator evidence and are not silently dropped from the
scope record.

## Outputs

- input audit: `input/{manifest.json,coverage.json,report.md}`
- input JSONL: `input/input.jsonl`
- missing JSONL: `input/missing.jsonl`
- universe JSONL: `input/universe.jsonl`
- shards: `input/shards.jsonl`
- input validation: `input/validation/`
- crop records: `crops/`
- crop PNGs: `local_dataset/qwen_vl_crops/full_validation/`
- runtime shard manifests: `runtime/manifests/`
- runtime progress/completed rows: `runtime/progress/`
- aggregated validation: `validation/{raw_response.jsonl,predictions.jsonl,completed.jsonl,contract/}`
- adapter export: `adapter/{predictions.jsonl,ground_truth.jsonl,manifest.json,report.md}`
- geometry join: `geometry/{verification.jsonl,manifest.json,report.md}`
- metrics/controls: `metrics/{metrics.json,summary.md}`
- bootstrap CI: `bootstrap_ci/{summary.json,summary.md}`
- failure rows: `failure_rows/{rows.jsonl,summary.json,report.md}`
- deterministic qualitative cases: `failure_cases/{queue.jsonl,inspection.md,inspection.json}`

## Downstream Results

Contract validation parsed `46,506/46,506` rows with 0 input errors, 0 output
errors, and 0 warnings. Adapter export produced `35,131` predictions, including
`32,236` in-scope H001-family predictions. The exact-label H001-family GT
denominator remains `3,972`; Qwen exact-label hits cover `1,453` GT keys.

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.2815 | 0.3600 | 0.1226 | 0.1246 |
| `probabilistic_recalibrated` | 0.3215 | 0.3653 | 0.0795 | 0.1166 |
| `rule_verified_point_subtype` | 0.3009 | 0.3630 | 0.0000 | 0.0000 |
| `control_family_specific_p_geom_valid` | 0.3379 | 0.3653 | 0.0510 | 0.1113 |

Bootstrap CI supports the same mechanism at top-50: probabilistic
recalibration improves R@50 by `+4.00 pp` and reduces V@50 by `-4.31 pp`
relative to semantic-only. The @100 recall gain is small (`+0.53 pp`) and
V@100 reduction is modest (`-0.80 pp`), so this branch should not be treated as
a stronger main-source result than VL-SAT or Open3DSG.

Failure-analysis rows are ready with `31,881` metric-eligible diagnostic rows
and `3,939` visual-audit queue rows. The deterministic qualitative inspection
selected 36 cases: 27 were demoted by geometry-aware reranking, 9 were promoted
or retained, and 6 rule-violated rows still had `p_geom_valid > 0.9`, preserving
the residual calibration-risk caveat.

## Paper Claim Boundary

Qwen full-validation now supports the H001 failure mechanism as a modern VLM
third-source extension: semantic crop-based relation predictions also contain
geometry-contradicting high-ranked rows, and the same calibrated geometry signal
reduces violations. Current AAAI decision on 2026-06-12 KST: keep Qwen as
appendix/extension evidence, not a main/table source, because its
full-validation recall is much lower than VL-SAT and Open3DSG and it is not an
end-to-end 3DSSG reproduction.

## Next Gate

No additional Qwen downstream experiment is required for the current AAAI claim.
Use the completed bundle only as appendix/extension evidence for the current
AAAI route.
