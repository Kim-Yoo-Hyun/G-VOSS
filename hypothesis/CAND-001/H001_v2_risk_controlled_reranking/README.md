# H001_v2 Risk-Controlled Reranking

Last updated: 2026-06-22 KST

H001_v2 is a hypothesis-stage extension of H001/GeoCalib. It keeps the core
H001 setting intact: existing relation-source predictions are joined with
frozen geometry evidence, and the method operates as a reliability layer rather
than a new 3D Scene Graph generator.

The change is narrow but principled:

```text
H001_v1: ranking_score = semantic_score * p_geom_valid
H001_v2: maximize semantic utility under a predeclared geometry-violation risk bound
```

## Branch Boundary

- Do not modify H001/GeoCalib locked experiment outputs, paper tables, or
  manuscript files from this branch.
- Do not choose thresholds from full-validation source metrics.
- Do not promote H001_v2 to the current paper main claim unless the user
  explicitly reopens the H001 paper route after protocol and evaluation gates.
- H001_v2 may read existing H001 prediction/geometry/metric artifacts only
  through a documented read-only source inventory.

## Current Dry Run Result

Calibration-only threshold selection is complete under:

`artifacts/calibration_threshold_selection/`

Primary result:

- `tau* = 0.20`
- equivalent threshold: `p_geom_valid >= 0.80`
- held-out calibration rows used: 1,193 `role == "dev"` rows
- selected rows: 423
- violations: 13
- empirical violation rate: 0.0307
- one-sided Clopper-Pearson upper bound: 0.0484
- primary budget: `alpha=0.05`, `delta=0.05`

This is an edge-level calibration threshold. Top-K `R@K` and `Violation@K`
must be evaluated only after applying this fixed threshold to source outputs.

## Reading Order

1. `01_overview.md`
2. `02_risk_control_protocol.md`
3. `03_dataset_and_artifact_contract.md`
4. `04_evaluation_plan.md`
5. `05_source_inventory.md`
6. `06_schema_probe.md`
7. `artifacts/calibration_threshold_selection/report.md`
8. `07_source_eval_contract.md`
9. `TODO.md`
