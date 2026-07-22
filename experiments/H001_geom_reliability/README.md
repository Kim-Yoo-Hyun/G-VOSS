# H001 Geometry Reliability Submission Artifacts

Last updated: 2026-07-22 KST

This directory is the compact experiment subset used by the RelCompat3D
manuscript and technical supplement. The canonical method pointer is
`active_method.json`; paper-facing summaries are indexed in
`results/h001_geom_reliability/`.

## Included Scope

- `no_family_indicator_v1/fit/`: frozen Linear and MLP model artifacts, score
  contract, diagnostics, and hashes.
- `no_family_indicator_v1/protocols/`: frozen protocols for the reported main
  results, controls, intervals, audits, runtime, and transfer stress test.
- `no_family_indicator_v1/evaluation/`: compact manifests, tables, summaries,
  model files, and mechanism rows used by the paper and supplement.
- `factor_isolation_protocol/{frozen_v1,fitted_v1}/`: compact protocol and
  fitted-model evidence for factor separation.
- `train_only_reestablishment_v1/`: split firewall, train-only fit lock,
  calibration model, and provenance records.

The active evaluation directories are:

- `routed_comparators`: Table 1 and Recall--Violation trajectories;
- `routed_ablation` and `mlp_ablation`: Linear and MLP controls;
- `scan_cluster` and `structured_scan_cluster`: paired scan-resampling results;
- `surface_audit` and `mlp_surface_audit`: point/mesh audit summaries;
- `structured_main`, `support_routing`, and `open3dsg_route`: all-family and
  coverage sensitivities;
- `held_out_primitive` and `counterfactual_sensitivity`: construct and policy
  sensitivity analyses;
- `runtime`: CPU re-ranking benchmark;
- `external_transfer`: ReplicaSSG/FROSS transfer stress test.

Large row-level predictions, geometry/verifier JSONL files, point/mesh
measurements, feature caches, checkpoints, and raw datasets are intentionally
not part of the submission repository. Compact outputs can be inspected
without them. Exact metric or source-inference reruns require the external
payloads documented in `docs/reproducibility.md`.

## Active Locks

`active_method.json` records the promoted protocol, model, score-contract, MLP
control, and MLP audit hashes. The method root is
`no_family_indicator_v1/`. `RelCompat3D-Linear` uses family-specific heads;
`RelCompat3D-MLP` is the shared compact nonlinear estimator. Neither
compatibility estimator uses predictor identity or the source relation score.

The paper evaluates fixed predictions from VL-SAT, Open3DSG, and SGFN on the
shared 3DSSG target. The evidence supports this scoped claim; the external
transfer artifact is a stress test, not established dataset-level
generalization.

## Reproduction Entry Points

The focused Docker configuration is `configs/h001/compose.structured.yaml`.
After mounting the required external inputs, run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm no_family_indicator_fit
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm no_family_indicator_freeze_initial
bash scripts/run_no_family_indicator_v1.sh initial
bash scripts/run_no_family_indicator_v1.sh downstream
```

Additional MLP, runtime, and transfer commands are listed in `commands.md`.
The wrapper refuses to overwrite a nonempty incomplete output and skips an
output whose manifest is already marked complete.

## Archive Boundary

The pre-cleanup local snapshot is under
`archive/local/pre_submission_20260722/previous_archive/experiments/`. It is
ignored and is not part of the submission GitHub tree.
Historical experiments, raw inputs, and candidate-paper duplicates must not be
used as current paper evidence unless explicitly restored and re-promoted.
