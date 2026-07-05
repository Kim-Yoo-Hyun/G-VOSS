# p_obs / p_rel Calibration Upgrade

## Role

This folder owns the upgraded p_obs / p_rel runtime check after the first
selective-decision stress test.

It adds:

- fixed train/calibration/evaluation split usage
- p_rel calibration selection without tuning on official validation
- actual asset observability audit from local 3RScan visual/mesh files
- calibration metrics and bootstrap CI
- selective prediction metrics
- missing-evidence controls, including wrong-pair evidence
- route-level failure connection for support/contact, attachment, and containment

## Current Status

```text
status = h002_pobs_prel_calibration_upgrade_ready
review_status = h002_pobs_prel_calibration_upgrade_result_review_after_runner_ready
validation_errors = 0
calibrated_quantitative_claim_pass = false
pobs_prel_framework_component_allowed = true
official_test_used = false
calibration_split = internal_dev
```

## Latest Runtime

```text
experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/
```

Key files:

| File | Role |
| --- | --- |
| `summary.json` | compact run status, row counts, selected calibrators, and pass checks |
| `calibration_metrics.csv` | ECE, Brier, NLL, AUROC, and calibration counts |
| `calibrator_selection.csv` | internal-dev calibrator selection record |
| `risk_coverage_curve.csv` | selective prediction coverage-risk curve |
| `missing_evidence_control_metrics.csv` | no-view, low-visibility, missing-mesh, shuffled-view, wrong-pair controls |
| `failure_route_connection.csv` | route-level support/contact, attachment, containment availability |
| `bootstrap_ci.csv` | bootstrap confidence intervals |
| `observability_asset_audit_labels.csv` | asset-derived observability audit labels |
| `prediction_scores.jsonl` | row-level calibrated scores |
| `validation_errors.jsonl` | runtime validation errors; expected to be empty |

## Latest Review Artifact

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/
  compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/
```

## Boundary

This run supports p_obs / p_rel as a framework component and stress-test layer.
It does not support the claim that calibrated p_obs / p_rel reliability is
solved.

Main blockers:

- asset audit produced only observable labels, so real unobservable/ambiguous
  observability labels are still missing
- p_rel calibrated ECE worsened on official validation
- attachment and containment empirical rows are absent from this runtime
- missing-evidence controls remain controlled stress tests, not full real-world
  missing-evidence coverage
