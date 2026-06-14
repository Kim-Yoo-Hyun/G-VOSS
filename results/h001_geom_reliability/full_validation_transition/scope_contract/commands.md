# Full Official Validation Commands

Status: `full_official_validation_scope_contract_ready_no_metric_execution`

Run from the repository root. These commands are a frozen protocol template, not
completed metric evidence. Use `tmux` and timestamped logs for long jobs.

## Scope Contract

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm full_validation_scope_contract'
```

Expected files:

- `results/h001_geom_reliability/full_validation_transition/scope_contract/manifest.json`
- `results/h001_geom_reliability/full_validation_transition/scope_contract/scope_contract.json`
- `results/h001_geom_reliability/full_validation_transition/scope_contract/scans.txt`
- `results/h001_geom_reliability/full_validation_transition/scope_contract/contexts.jsonl`
- `results/h001_geom_reliability/full_validation_transition/scope_contract/commands.md`
- `results/h001_geom_reliability/full_validation_transition/scope_contract/report.md`

## VL-SAT Full Validation Route

Docker-compatible staging/runtime/preflight is now frozen under:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
```

Current status: `vlsat_full_validation_runtime_record_ready_no_metric_execution`.
The stage and raw preflight are ready with 157/157 faithful staged scans,
runtime image `h001-open3dsg-repro:cu128`, 16/16 checkpoint files, raw preflight
`ready_to_run`, 0 errors, and 1 expected legacy import-shim warning.

Authoritative commands now live in:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/runtime_record/commands.md
```

Launch the raw dump only as the documented timestamped tmux/background Docker
job when GPU contention with the running Open3DSG R1 training job is acceptable.
The raw dump is still not metric evidence until adapter export, ground-truth
JSONL, geometry join, metrics, controls, GT verifier check, bootstrap CI, and
table/report regeneration are all rerun under this same full-validation scope.

## Open3DSG Full Validation Route

Use separate runtime/output paths. Do not overwrite the current H001
`377/388` averaged-BLIP artifacts.

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_full_validation_payload'
```

Planned output root:

- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/payload`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/views`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/preprocess`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/features`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_dump`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_dump_identity`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/adapter`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/geometry`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/metrics`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/bootstrap_ci`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/failure_rows`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/paper_caveats`

Planned runtime root: `local_dataset/Open3DSG_staged/h001_full_validation_runtime`.

Checkpoint rule: use the selected non-avg checkpoint only if R1 completes and
checkpoint selection is refreshed before downstream evaluation; otherwise keep
the averaged-BLIP caveat.
