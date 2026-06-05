# VL-SAT full-validation Qualitative Failure Case Sample

Status: `failure_case_sample_ready`
Created at: `2026-06-05T01:26:03.017801+00:00`

## Scope

This sample is selected from high-severity VL-SAT full-validation failure-analysis rows with `needs_visual_audit=true`.
It is a qualitative inspection queue, not an additional metric.

## Summary

- selected cases: `36`
- candidate rows: `2897`
- source rows: `59841`

## Selected Counts

### By Category

- `geometry_contradiction`: 14
- `semantic_and_geometry_failure`: 22

### By Predicate Family

- `proximity`: 6
- `relative_vertical`: 20
- `support_contact`: 10

### By Top-k Transition

- `demoted_out_of_top100`: 16
- `demoted_out_of_top50`: 6
- `promoted_into_top100`: 4
- `promoted_into_top50`: 4
- `stayed_in_topk`: 6

## First Cases

| case | category | family | predicate | pair | transition | delta |
| --- | --- | --- | --- | --- | --- | --- |
| `vlsat_case_001` | `geometry_contradiction` | `proximity` | `close by` | table -> table | `demoted_out_of_top50` | `10` |
| `vlsat_case_002` | `geometry_contradiction` | `proximity` | `close by` | box -> book | `demoted_out_of_top100` | `20` |
| `vlsat_case_003` | `geometry_contradiction` | `proximity` | `close by` | heater -> trash can | `stayed_in_topk` | `22` |
| `vlsat_case_004` | `geometry_contradiction` | `relative_vertical` | `lower than` | box -> box | `demoted_out_of_top50` | `294` |
| `vlsat_case_005` | `geometry_contradiction` | `relative_vertical` | `lower than` | box -> box | `demoted_out_of_top100` | `226` |
| `vlsat_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | lamp -> showcase | `promoted_into_top50` | `-17` |
| `vlsat_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | plant -> fireplace | `promoted_into_top100` | `-60` |
| `vlsat_case_008` | `geometry_contradiction` | `relative_vertical` | `lower than` | shelf -> magazine rack | `stayed_in_topk` | `35` |
| `vlsat_case_009` | `geometry_contradiction` | `support_contact` | `lying on` | commode -> floor | `demoted_out_of_top50` | `34` |
| `vlsat_case_010` | `geometry_contradiction` | `support_contact` | `standing on` | light -> towel | `demoted_out_of_top100` | `63` |
| `vlsat_case_011` | `geometry_contradiction` | `support_contact` | `supported by` | curtain -> wall | `promoted_into_top50` | `-15` |
| `vlsat_case_012` | `geometry_contradiction` | `support_contact` | `lying on` | wall -> floor | `promoted_into_top100` | `-31` |
| `vlsat_case_013` | `geometry_contradiction` | `support_contact` | `standing on` | shelf -> shelf | `stayed_in_topk` | `30` |
| `vlsat_case_014` | `semantic_and_geometry_failure` | `proximity` | `close by` | bookshelf -> ceiling | `demoted_out_of_top50` | `39` |
| `vlsat_case_015` | `semantic_and_geometry_failure` | `proximity` | `close by` | coffee table -> ceiling | `demoted_out_of_top100` | `150` |
| `vlsat_case_016` | `semantic_and_geometry_failure` | `proximity` | `close by` | shelf -> towel | `stayed_in_topk` | `30` |
| `vlsat_case_017` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | shelf -> laundry basket | `demoted_out_of_top50` | `224` |
| `vlsat_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | lamp -> toilet paper dispenser | `demoted_out_of_top100` | `308` |
| `vlsat_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | blanket -> floor | `promoted_into_top50` | `-22` |
| `vlsat_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | shelf -> tv stand | `promoted_into_top100` | `-55` |

## Outputs

- `queue_jsonl`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/queue.jsonl`
- `manifest_json`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/report.md`

## Claim Boundary

Use these cases to choose visual examples and write failure narratives.
Do not report them as a statistically representative audit without a separate labeling protocol.
