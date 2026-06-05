# VL-SAT Raw Dump

Created at: `2026-06-03`
Status: `ready_to_run`
Baseline run id: `vlsat_full_official_validation_frozen_v1`

## Inputs

- VL-SAT code root: `local_dataset/VLSAT_code/CVPR2023-VLSAT`
- Staged root: `local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT`
- Selection file: `experiments/H001_geom_reliability/full_validation_transition/scope_contract/scans.txt`
- Checkpoint root: `local_dataset/VLSAT_code/CVPR2023-VLSAT/output`

## Outputs

- Raw dump: `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight/raw.jsonl`
- Runtime config: `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight/config.json`
- Summary: `summary.json`

## Counts

- Selected scans: `157`
- Dumped subgraphs: `0`
- Directed pairs: `0`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `1`

### Warnings

- `src_lib_pointnet_graph_missing_using_unused_import_shim`

## Guardrails

- This raw dump is source-run data for the selected scan split named by the command.
- It must not be used to fit `p_geom_valid`.
- Raw scores alone are not metric evidence until prediction export, ground-truth JSONL, geometry join, calibrator/verifier outputs, metrics, controls, and bootstrap outputs exist.
