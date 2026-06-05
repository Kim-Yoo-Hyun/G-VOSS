# Open3DSG recovery full-validation Qualitative Failure Case Sample

Status: `failure_case_sample_ready`
Created at: `2026-06-05T01:26:03.888372+00:00`

## Scope

This sample is selected from high-severity Open3DSG recovery full-validation failure-analysis rows with `needs_visual_audit=true`.
It is a qualitative inspection queue, not an additional metric.

## Summary

- selected cases: `36`
- candidate rows: `8821`
- source rows: `82155`

## Selected Counts

### By Category

- `geometry_contradiction`: 13
- `semantic_and_geometry_failure`: 23

### By Predicate Family

- `proximity`: 7
- `relative_vertical`: 19
- `support_contact`: 10

### By Top-k Transition

- `demoted_out_of_top100`: 6
- `demoted_out_of_top50`: 15
- `promoted_into_top100`: 6
- `promoted_into_top50`: 4
- `stayed_in_topk`: 5

## First Cases

| case | category | family | predicate | pair | transition | delta |
| --- | --- | --- | --- | --- | --- | --- |
| `open3dsg_recovery_case_001` | `geometry_contradiction` | `proximity` | `close by` | heater -> trash can | `demoted_out_of_top50` | `244` |
| `open3dsg_recovery_case_002` | `geometry_contradiction` | `proximity` | `close by` | object -> doorframe | `demoted_out_of_top100` | `183` |
| `open3dsg_recovery_case_003` | `geometry_contradiction` | `proximity` | `close by` | shelf -> shelf | `promoted_into_top100` | `-35` |
| `open3dsg_recovery_case_004` | `geometry_contradiction` | `relative_vertical` | `higher than` | floor -> rack | `demoted_out_of_top50` | `398` |
| `open3dsg_recovery_case_005` | `geometry_contradiction` | `relative_vertical` | `higher than` | books -> lamp | `demoted_out_of_top100` | `346` |
| `open3dsg_recovery_case_006` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top50` | `-298` |
| `open3dsg_recovery_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top100` | `-343` |
| `open3dsg_recovery_case_008` | `geometry_contradiction` | `relative_vertical` | `lower than` | ceiling -> wall | `stayed_in_topk` | `49` |
| `open3dsg_recovery_case_009` | `geometry_contradiction` | `support_contact` | `lying on` | lamp -> side table | `demoted_out_of_top50` | `362` |
| `open3dsg_recovery_case_010` | `geometry_contradiction` | `support_contact` | `lying on` | suitcase -> kitchen counter | `demoted_out_of_top100` | `263` |
| `open3dsg_recovery_case_011` | `geometry_contradiction` | `support_contact` | `supported by` | item -> refrigerator | `promoted_into_top50` | `-231` |
| `open3dsg_recovery_case_012` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top100` | `-289` |
| `open3dsg_recovery_case_013` | `geometry_contradiction` | `support_contact` | `standing on` | kitchen cabinet -> kitchen cabinet | `stayed_in_topk` | `33` |
| `open3dsg_recovery_case_014` | `semantic_and_geometry_failure` | `proximity` | `close by` | heater -> item | `demoted_out_of_top50` | `393` |
| `open3dsg_recovery_case_015` | `semantic_and_geometry_failure` | `proximity` | `close by` | shoes -> frame | `demoted_out_of_top100` | `366` |
| `open3dsg_recovery_case_016` | `semantic_and_geometry_failure` | `proximity` | `close by` | pillow -> wall | `promoted_into_top100` | `-43` |
| `open3dsg_recovery_case_017` | `semantic_and_geometry_failure` | `proximity` | `close by` | plant -> cabinet | `stayed_in_topk` | `-31` |
| `open3dsg_recovery_case_018` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> ceiling | `demoted_out_of_top50` | `431` |
| `open3dsg_recovery_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | bag -> vase | `demoted_out_of_top100` | `379` |
| `open3dsg_recovery_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `lower than` | clutter -> floor | `promoted_into_top50` | `-295` |

## Outputs

- `queue_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/queue.jsonl`
- `manifest_json`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/report.md`

## Claim Boundary

Use these cases to choose visual examples and write failure narratives.
Do not report them as a statistically representative audit without a separate labeling protocol.
