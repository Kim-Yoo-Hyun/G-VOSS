# H001_v2 Risk-Controlled Reranking

Last updated: 2026-06-24 KST

H001_v2 is a method-framing extension of H001/GeoCalib. It keeps the core H001
setting intact: existing relation-source predictions are joined with frozen
geometry evidence, and the method operates as a reliability layer rather than a
new 3D Scene Graph generator.

The base framing is narrow but principled:

```text
GeoCalib score = semantic_score * p_geom_valid
               = exp(log semantic_score - geometry_risk)
geometry_risk = -log p_geom_valid
```

Thus the current deployed score is the `lambda=1` instance of risk-aware soft
reranking. The earlier fixed-`tau*` hard-threshold experiment remains a
diagnostic variant, not the current main method.

The current H001_v2 development direction is family-conditional calibrated
geometry risk:

```text
p_geom_valid_family = C_family(phi(g))
GeoCalib-family score = semantic_score * p_geom_valid_family
```

This is a stronger method direction than a single pooled `lambda` because
geometry validity has different semantics for support/contact, proximity, and
relative-vertical relations.

## Branch Boundary

- Do not modify H001/GeoCalib locked experiment outputs, paper tables, or
  manuscript files from this branch.
- Do not choose thresholds from full-validation source metrics.
- Do not promote fixed-`tau*` H001_v2 to the current paper main claim. Any
  future H001_v2 method work must be a separate protocol revision, not a
  main-table replacement for the current GeoCalib result.
- H001_v2 may read existing H001 prediction/geometry/metric artifacts only
  through a documented read-only source inventory.

## Current Threshold Result

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

## Current Source Evaluation Result

Fixed-threshold source point metrics are complete under:

`artifacts/source_eval/`

Summary:

- VL-SAT: H001_v2 is not competitive with `probabilistic_recalibrated`; recall
  drops strongly and V@100 is slightly worse than `semantic_only`.
- Open3DSG: H001_v2 improves strongly over `semantic_only`, but is mixed against
  `probabilistic_recalibrated`.
- Tau corruption controls are complete. Replacing real edge geometry with
  shuffled or wrong-pair geometry degrades recall and increases violation on
  both sources, so the fixed-threshold signal is geometry-specific.
- Current judgment: `diagnostic_candidate_locked`; keep H001_v2 fixed-`tau*`
  as diagnostic evidence only and keep the current H001/GeoCalib paper main
  results unchanged.
- Method-framing update: the current GeoCalib `semantic_score * p_geom_valid`
  result is now interpreted as risk-aware soft reranking. The follow-up method
  direction is family-conditional calibrated geometry risk rather than the fixed
  hard threshold.
- Lambda-soft update: a calibration-dev-selected pooled soft penalty was tested
  as `semantic_score * p_geom_valid^lambda` with `lambda*=1.25`. The result is
  geometry-specific but mixed against the current `lambda=1`
  `probabilistic_recalibrated` condition, so it is diagnostic only and does not
  replace the current main paper table.
- Family-conditional risk update: the existing `family_specific_p_geom_valid`
  artifact is now formalized as a family-conditional calibrated geometry-risk
  operating point, not a generic control. It is frozen from train/dev
  calibration rows, uses no held-out source metric tuning, improves Open3DSG
  recall and violation across K against pooled risk, and reduces VL-SAT
  violation with near-flat recall.

## Reading Order

1. `01_overview.md`
2. `02_risk_control_protocol.md`
3. `03_dataset_and_artifact_contract.md`
4. `04_evaluation_plan.md`
5. `05_source_inventory.md`
6. `06_schema_probe.md`
7. `artifacts/calibration_threshold_selection/report.md`
8. `07_source_eval_contract.md`
9. `08_source_eval_result.md`
10. `09_risk_aware_soft_reranking.md`
11. `10_lambda_soft_reranking_result.md`
12. `11_family_conditional_risk_result.md`
13. `TODO.md`
