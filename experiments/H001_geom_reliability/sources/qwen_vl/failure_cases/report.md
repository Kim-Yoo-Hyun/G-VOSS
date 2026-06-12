# Qwen-VL full-source Qualitative Failure Case Sample

Status: `failure_case_sample_ready`
Created at: `2026-06-11T03:01:13.253275+00:00`

## Scope

This sample is selected from high-severity Qwen-VL full-source failure-analysis rows with `needs_visual_audit=true`.
It is a qualitative inspection queue, not an additional metric.

## Summary

- selected cases: `36`
- candidate rows: `2843`
- source rows: `22787`

## Selected Counts

### By Category

- `geometry_contradiction`: 10
- `semantic_and_geometry_failure`: 26

### By Predicate Family

- `proximity`: 4
- `relative_vertical`: 23
- `support_contact`: 9

### By Top-k Transition

- `demoted_out_of_top100`: 5
- `demoted_out_of_top50`: 19
- `promoted_into_top100`: 3
- `promoted_into_top50`: 4
- `stayed_in_topk`: 5

## First Cases

| case | category | family | predicate | pair | transition | delta |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen_vl_case_001` | `geometry_contradiction` | `proximity` | `close by` | vase -> bread | `demoted_out_of_top50` | `69` |
| `qwen_vl_case_002` | `geometry_contradiction` | `relative_vertical` | `higher than` | window -> ceiling | `demoted_out_of_top50` | `107` |
| `qwen_vl_case_003` | `geometry_contradiction` | `relative_vertical` | `higher than` | carpet -> plant | `demoted_out_of_top100` | `49` |
| `qwen_vl_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | towel -> shower | `promoted_into_top50` | `-97` |
| `qwen_vl_case_005` | `geometry_contradiction` | `relative_vertical` | `lower than` | heater -> floor | `promoted_into_top100` | `-77` |
| `qwen_vl_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | heater -> wall | `stayed_in_topk` | `-45` |
| `qwen_vl_case_007` | `geometry_contradiction` | `support_contact` | `supported by` | kitchen counter -> oven | `demoted_out_of_top50` | `45` |
| `qwen_vl_case_008` | `geometry_contradiction` | `support_contact` | `supported by` | drying machine -> washing machine | `demoted_out_of_top100` | `20` |
| `qwen_vl_case_009` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top50` | `-31` |
| `qwen_vl_case_010` | `geometry_contradiction` | `support_contact` | `supported by` | ceiling -> wall | `stayed_in_topk` | `-34` |
| `qwen_vl_case_011` | `semantic_and_geometry_failure` | `proximity` | `close by` | socket -> pack | `demoted_out_of_top50` | `54` |
| `qwen_vl_case_012` | `semantic_and_geometry_failure` | `proximity` | `close by` | shelf -> vase | `demoted_out_of_top100` | `36` |
| `qwen_vl_case_013` | `semantic_and_geometry_failure` | `proximity` | `close by` | pack -> socket | `stayed_in_topk` | `17` |
| `qwen_vl_case_014` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `demoted_out_of_top50` | `151` |
| `qwen_vl_case_015` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | box -> window | `demoted_out_of_top100` | `88` |
| `qwen_vl_case_016` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | pillow -> floor | `promoted_into_top50` | `-81` |
| `qwen_vl_case_017` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | tv -> wall | `promoted_into_top100` | `-65` |
| `qwen_vl_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> wall | `stayed_in_topk` | `47` |
| `qwen_vl_case_019` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | floor -> wall | `demoted_out_of_top50` | `123` |
| `qwen_vl_case_020` | `semantic_and_geometry_failure` | `support_contact` | `supported by` | box -> window | `demoted_out_of_top100` | `82` |

## Outputs

- `queue_jsonl`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_cases/queue.jsonl`
- `manifest_json`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_cases/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/qwen_vl/failure_cases/report.md`

## Claim Boundary

Use these cases to choose visual examples and write failure narratives.
Do not report them as a statistically representative audit without a separate labeling protocol.
