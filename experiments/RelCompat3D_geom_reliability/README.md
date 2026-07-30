# RelCompat3D Geometry Reliability Submission Artifacts

Last updated: 2026-07-27 KST

This directory is the compact experiment subset used by the RelCompat3D
manuscript and technical supplement. The canonical method pointer is
`active_method.json`; paper-facing summaries are indexed in
`results/relcompat3d_geom_reliability/`.

## Included Scope

- `no_family_indicator_v1/fit/`: score contract, diagnostics, and model hashes.
  Fitted parameter files are restored from the Drive model archive and remain
  ignored by Git.
- `no_family_indicator_v1/protocols/`: frozen protocols for the reported main
  results, controls, intervals, audits, runtime, and transfer stress test.
- `no_family_indicator_v1/evaluation/`: compact manifests, tables, summaries,
  model hashes, and mechanism rows used by the paper and supplement.
- `factor_isolation_protocol/{frozen_v1,fitted_v1}/`: compact protocol,
  fitted-model hashes, and evidence for factor separation.
- `train_only_reestablishment_v1/`: split firewall, train-only fit lock,
  calibration-model hash, and provenance records.
- `score_robustness_v1/`: frozen P0-1 source-score mapping sensitivity and
  P0-2 closest-simple-baseline protocol, Docker command, and compact outputs.
- `routing_controls_v1/`: P0-3 matched family-slot routing controls on the
  canonical candidate pool.
- `construct_dependence_v1/`: P0-4 dependency matrix and hash-verified index
  of feature-removal, uncertainty-policy, component, and point/mesh evidence.
- `component_diagnostics_v1/`: matched Linear/MLP pairwise-loss and
  transformation-averaging diagnostics.
- `seed_robustness_v1/`: five predeclared fitting-seed executions and
  predictor-by-\(K\) variation summaries.
- `row_reproduction_v1/`: pseudonymized row schema, licensed-input exporter,
  one-command paper-table/figure reproducer, and exact canonical-cell checks.
- `candidate_oracle_v1/`: fixed-candidate coverage and unconstrained,
  family-slot, and active-route Recall upper bounds.

The active evaluation directories are:

- `routed_comparators`: Table 1 and Recall--Violation trajectories;
- `routed_ablation` and `mlp_ablation`: Linear and MLP controls;
- `scan_cluster` and `structured_scan_cluster`: paired scan-resampling results;
- `surface_audit` and `mlp_surface_audit`: point/mesh audit summaries;
- `structured_main`, `support_routing`, and `open3dsg_route`: all-family and
  coverage sensitivities;
- `held_out_primitive` and `counterfactual_sensitivity`: construct and policy
  sensitivity analyses;
- `component_removals`: direct Linear removals of the linked pairwise loss and
  inference-time transformation averaging;
- `runtime`: CPU re-ranking benchmark;
- `external_transfer`: ReplicaSSG/FROSS transfer stress test.

The post-hoc P0 and robustness directories are separate from the promoted
method root. Score robustness, routing controls, component diagnostics, and
the active-seed checks must reproduce the active Source, Linear, and MLP
points exactly. None changes `active_method.json`.

Large source prediction, geometry/verifier JSONL, point/mesh measurements,
feature caches, checkpoints, and raw datasets are intentionally not part of
the submission repository. The row-reproduction exporter derives a
pseudonymized bundle that excludes original identifiers and raw geometry, but
public redistribution of that bundle remains held until the 3RScan/3DSSG data
terms are confirmed. Compact regenerated tables, figure data, validation
reports, and oracle summaries are included. Exact reruns from the licensed
inputs follow `docs/reproducibility.md`.

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

The focused Docker configuration is `configs/relcompat3d/compose.structured.yaml`.
After mounting the required external inputs, run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_fit
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_freeze_initial
bash scripts/run_no_family_indicator_v1.sh initial
bash scripts/run_no_family_indicator_v1.sh downstream
```

Additional MLP, runtime, and transfer commands are listed in `commands.md`.
The wrapper refuses to overwrite a nonempty incomplete output and skips an
output whose manifest is already marked complete.

The paper-facing row reproduction and candidate-pool oracle use:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm relcompat3d_export_rows
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm relcompat3d_reproduce_rows
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm relcompat3d_candidate_oracle
```

Fresh reruns write to `row_reproduction_v1/regenerated/` and
`candidate_oracle_v1/regenerated/`. The tracked `evaluation/` directories
remain the frozen paper references.

The reproducer checks 291 canonical cells from Tables 1--3 with tolerance
\(10^{-12}\); the completed run has maximum absolute error zero. The
candidate-pool oracle is a diagnostic upper bound and does not modify the
active models or ranking rule.

## Archive Boundary

The pre-cleanup local snapshot is under
`archive/local/pre_submission_20260722/previous_archive/experiments/`. It is
ignored and is not part of the submission GitHub tree.
Historical experiments, raw inputs, and candidate-paper duplicates must not be
used as current paper evidence unless explicitly restored and re-promoted.
