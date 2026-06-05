# Full-Validation Artifact Bundle Plan

Status: `full_validation_artifact_bundle_plan_ready_no_archive_created`

This folder records the paper-facing full-validation artifact bundle plan. It
does not create the archive yet. The archive should be generated only when an
upload/release package is needed, because packaging row-level JSONL can be an
I/O-heavy job.

## Included Sources

| Source | Role | Rows / cases |
| --- | --- | ---: |
| VL-SAT full-validation | controlled anchor | 957,008 predictions, 957,008 geometry rows, 59,841 failure rows, 36 qualitative cases |
| Open3DSG recovery full-validation | primary open-vocabulary source | 26,938 raw rows, 695,916 predictions, 695,916 geometry rows, 82,155 failure rows, 36 qualitative cases |

The Open3DSG bundle includes the selected official non-avg checkpoint
`epoch=13-step=13104.ckpt` with sha256
`ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb`.

## Boundary

The bundle supports the current full-validation H001 claim only. It does not
include raw 3RScan, large feature caches, Qwen-VL model cache, or the optional
Qwen/attachment/relative-horizontal extension outputs.
