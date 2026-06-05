# VL-SAT Full-Validation Runtime Record

Generated: `2026-06-03T09:27:55+00:00`
Status: `vlsat_full_validation_runtime_record_ready_no_metric_execution`

## Scope

- selected scans: `157`
- contexts: `548`
- expected VL-SAT prediction rows: `957008`
- H001-family GT rows: `3972`

## Runtime

- runtime image: `h001-open3dsg-repro:cu128`
- staged root: `local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT`
- VL-SAT code root: `local_dataset/VLSAT_code/CVPR2023-VLSAT`
- checkpoint root: `local_dataset/VLSAT_code/CVPR2023-VLSAT/output/ckp/Mmgnet/3dssg`

## Readiness

- stage status: `ready`
- faithful ready scans: `157`
- raw preflight status: `ready_to_run`
- raw preflight errors: `0`
- raw preflight warnings: `1`
- checkpoint files present: `16/16`

## Blockers

- none

## Next

1. Launch the raw dump as the documented timestamped tmux/background job when GPU contention is acceptable.
2. After raw dump completion, run adapter export, ground-truth JSONL, geometry join, metrics, controls, GT verifier check, bootstrap CI, and table/report regeneration.
3. Do not update paper tables until downstream full-validation metrics and bootstrap CI are regenerated.
