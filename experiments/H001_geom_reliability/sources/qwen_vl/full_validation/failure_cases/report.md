# Qwen-VL full official validation Qualitative Failure Case Sample

Status: `failure_case_sample_ready`
Created at: `2026-06-11T18:18:10.861728+00:00`

## Scope

This sample is selected from high-severity Qwen-VL full official validation failure-analysis rows with `needs_visual_audit=true`.
It is a qualitative inspection queue, not an additional metric.

## Summary

- selected cases: `36`
- candidate rows: `3939`
- source rows: `31881`

## Selected Counts

### By Category

- `geometry_contradiction`: 10
- `semantic_and_geometry_failure`: 26

### By Predicate Family

- `proximity`: 5
- `relative_vertical`: 22
- `support_contact`: 9

### By Top-k Transition

- `demoted_out_of_top100`: 5
- `demoted_out_of_top50`: 18
- `promoted_into_top100`: 3
- `promoted_into_top50`: 5
- `stayed_in_topk`: 5

## First Cases

| case | category | family | predicate | pair | transition | delta |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen_vl_full_validation_case_001` | `geometry_contradiction` | `proximity` | `close by` | vase -> bread | `demoted_out_of_top50` | `69` |
| `qwen_vl_full_validation_case_002` | `geometry_contradiction` | `relative_vertical` | `higher than` | window -> ceiling | `demoted_out_of_top50` | `107` |
| `qwen_vl_full_validation_case_003` | `geometry_contradiction` | `relative_vertical` | `higher than` | carpet -> plant | `demoted_out_of_top100` | `49` |
| `qwen_vl_full_validation_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | towel -> shower | `promoted_into_top50` | `-97` |
| `qwen_vl_full_validation_case_005` | `geometry_contradiction` | `relative_vertical` | `lower than` | heater -> floor | `promoted_into_top100` | `-77` |
| `qwen_vl_full_validation_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | heater -> curtain | `stayed_in_topk` | `46` |
| `qwen_vl_full_validation_case_007` | `geometry_contradiction` | `support_contact` | `supported by` | kitchen counter -> oven | `demoted_out_of_top50` | `45` |
| `qwen_vl_full_validation_case_008` | `geometry_contradiction` | `support_contact` | `supported by` | drying machine -> washing machine | `demoted_out_of_top100` | `20` |
| `qwen_vl_full_validation_case_009` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top50` | `-31` |
| `qwen_vl_full_validation_case_010` | `geometry_contradiction` | `support_contact` | `supported by` | ceiling -> wall | `stayed_in_topk` | `-34` |
| `qwen_vl_full_validation_case_011` | `semantic_and_geometry_failure` | `proximity` | `close by` | tv stand -> box | `demoted_out_of_top50` | `125` |
| `qwen_vl_full_validation_case_012` | `semantic_and_geometry_failure` | `proximity` | `close by` | box -> decoration | `demoted_out_of_top100` | `44` |
| `qwen_vl_full_validation_case_013` | `semantic_and_geometry_failure` | `proximity` | `close by` | wall -> coffee table | `promoted_into_top50` | `-3` |
| `qwen_vl_full_validation_case_014` | `semantic_and_geometry_failure` | `proximity` | `close by` | pillow -> cabinet | `stayed_in_topk` | `17` |
| `qwen_vl_full_validation_case_015` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | `151` |
| `qwen_vl_full_validation_case_016` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | box -> window | `demoted_out_of_top100` | `88` |
| `qwen_vl_full_validation_case_017` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | pillow -> floor | `promoted_into_top50` | `-81` |
| `qwen_vl_full_validation_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | tv -> wall | `promoted_into_top100` | `-65` |
| `qwen_vl_full_validation_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> kitchen cabinet | `stayed_in_topk` | `48` |
| `qwen_vl_full_validation_case_020` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | floor -> wall | `demoted_out_of_top50` | `123` |

## Outputs

- `queue_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_cases/queue.jsonl`
- `manifest_json`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_cases/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_cases/report.md`

## Claim Boundary

Use these cases to choose visual examples and write failure narratives.
Do not report them as a statistically representative audit without a separate labeling protocol.
