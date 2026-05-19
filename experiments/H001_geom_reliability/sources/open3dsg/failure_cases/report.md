# Open3DSG Qualitative Failure Case Sample

Status: `failure_case_sample_ready`
Created at: `2026-05-18T10:52:05.607555+00:00`

## Scope

This sample is selected from high-severity Open3DSG failure-analysis rows with `needs_visual_audit=true`.
It is a qualitative inspection queue, not an additional metric.

## Summary

- selected cases: `36`
- candidate rows: `6162`
- source rows: `57736`

## Selected Counts

### By Category

- `geometry_contradiction`: 14
- `semantic_and_geometry_failure`: 22

### By Predicate Family

- `proximity`: 8
- `relative_vertical`: 18
- `support_contact`: 10

### By Top-k Transition

- `demoted_out_of_top100`: 6
- `demoted_out_of_top50`: 14
- `promoted_into_top100`: 6
- `promoted_into_top50`: 4
- `stayed_in_topk`: 6

## First Cases

| case | category | family | predicate | pair | transition | delta |
| --- | --- | --- | --- | --- | --- | --- |
| `open3dsg_case_001` | `geometry_contradiction` | `proximity` | `close by` | heater -> trash can | `demoted_out_of_top50` | `246` |
| `open3dsg_case_002` | `geometry_contradiction` | `proximity` | `close by` | heater -> side table | `demoted_out_of_top100` | `112` |
| `open3dsg_case_003` | `geometry_contradiction` | `proximity` | `close by` | table -> table | `promoted_into_top100` | `-43` |
| `open3dsg_case_004` | `geometry_contradiction` | `proximity` | `close by` | shelf -> shelf | `stayed_in_topk` | `31` |
| `open3dsg_case_005` | `geometry_contradiction` | `relative_vertical` | `higher than` | desk -> lamp | `demoted_out_of_top50` | `397` |
| `open3dsg_case_006` | `geometry_contradiction` | `relative_vertical` | `higher than` | books -> lamp | `demoted_out_of_top100` | `364` |
| `open3dsg_case_007` | `geometry_contradiction` | `relative_vertical` | `lower than` | chair -> floor | `promoted_into_top50` | `-289` |
| `open3dsg_case_008` | `geometry_contradiction` | `relative_vertical` | `lower than` | object -> cabinet | `promoted_into_top100` | `-335` |
| `open3dsg_case_009` | `geometry_contradiction` | `relative_vertical` | `lower than` | doorframe -> floor | `stayed_in_topk` | `-40` |
| `open3dsg_case_010` | `geometry_contradiction` | `support_contact` | `lying on` | lamp -> side table | `demoted_out_of_top50` | `380` |
| `open3dsg_case_011` | `geometry_contradiction` | `support_contact` | `lying on` | vase -> printer | `demoted_out_of_top100` | `253` |
| `open3dsg_case_012` | `geometry_contradiction` | `support_contact` | `supported by` | item -> refrigerator | `promoted_into_top50` | `-212` |
| `open3dsg_case_013` | `geometry_contradiction` | `support_contact` | `supported by` | box -> wardrobe | `promoted_into_top100` | `-282` |
| `open3dsg_case_014` | `geometry_contradiction` | `support_contact` | `lying on` | desk -> floor | `stayed_in_topk` | `27` |
| `open3dsg_case_015` | `semantic_and_geometry_failure` | `proximity` | `close by` | stool -> item | `demoted_out_of_top50` | `398` |
| `open3dsg_case_016` | `semantic_and_geometry_failure` | `proximity` | `close by` | pack -> clock | `demoted_out_of_top100` | `349` |
| `open3dsg_case_017` | `semantic_and_geometry_failure` | `proximity` | `close by` | pillow -> wall | `promoted_into_top100` | `-41` |
| `open3dsg_case_018` | `semantic_and_geometry_failure` | `proximity` | `close by` | blanket -> wall | `stayed_in_topk` | `-14` |
| `open3dsg_case_019` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | floor -> curtain | `demoted_out_of_top50` | `431` |
| `open3dsg_case_020` | `semantic_and_geometry_failure` | `relative_vertical` | `higher than` | shoes -> frame | `demoted_out_of_top100` | `381` |

## Outputs

- `queue_jsonl`: `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl`
- `manifest_json`: `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/manifest.json`
- `report_md`: `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/report.md`

## Claim Boundary

Use these cases to choose visual examples and write failure narratives.
Do not report them as a statistically representative audit without a separate labeling protocol.
