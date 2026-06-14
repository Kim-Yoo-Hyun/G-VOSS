# Method

Last updated: 2026-05-07

## Role

This document merges the former evidence schema, verifier, calibration,
evaluation protocol, and prediction-join contracts.

Merged former files:

- `02_evidence_verifier.md`
- `03_calibration.md`
- `04_protocol.md`
- `11_join.md`

## Evidence Schema

H001 stores relation-level evidence with stable identifiers:

| Field group | Purpose |
| --- | --- |
| scan/subgraph/pair ids | preserve object-pair identity across prediction, geometry, and GT joins |
| subject/object labels | support semantic interpretation and audit |
| predicate family | map raw predicates to `support_contact`, `proximity`, or `relative_vertical` |
| OBB geometry | provide scalable pair-level geometric features |
| point/local evidence | reduce support/contact false violations |
| verifier status/reason | expose `satisfied`, `uncertain`, or `violated` decision |
| `p_geom_valid` | calibrated geometry-valid probability used for reranking |

Primary predicate families:

- `support_contact`
- `proximity`
- `relative_vertical`

Unsupported or diagnostic families are not part of the scoped metric claim.

## Method Contribution Framing

H001 should be presented as a calibrated geometry-consistency evaluation and
re-ranking framework, not as a standalone verifier script.

Framework components:

| Component | Contribution role |
| --- | --- |
| identity-preserving prediction rows | makes semantic predictions, geometry evidence, and GT labels joinable |
| geometry evidence schema | exposes object-pair geometry as auditable relation evidence |
| subtype-aware verifier | converts geometry evidence into traceable satisfied/uncertain/violated decisions |
| `p_geom_valid` calibration | turns geometry consistency into a frozen probabilistic reliability signal |
| reliability-aware re-ranking/filtering | combines semantic score and calibrated geometry validity without replacing the base predictor |
| violation/recall evaluation layer | measures reliability gain separately from standard recall |

Primary paper wording:

```text
calibrated geometry-consistency evaluation and re-ranking for 3D scene graph
relations
```

Avoid this wording:

```text
a rule verifier script for VL-SAT
```

Rationale:

- the reusable unit is the prediction-row contract, geometry join, calibrated
  reliability score, and metric protocol;
- `VL-SAT` is the first reproduced predictor used to instantiate the framework;
- Open3DSG is the selected second-source path for testing whether the framework
  transfers beyond the first baseline.

## Verifier Contract

Verifier output:

```text
satisfied
uncertain
violated
```

Policy:

- use `violated` only when geometry evidence is strong enough;
- use `uncertain` for missing/weak point evidence, ambiguous support/contact,
  or scan geometry quality issues;
- avoid converting annotation noise directly into method failure.

Support/contact subtypes:

| Subtype | Reading |
| --- | --- |
| `legged_floor_support` | floor support through legs or sparse contact |
| `soft_support_contact` | soft or deformable support/contact |
| `rigid_object_on_furniture` | rigid object supported by furniture/surface |
| `geometry_quality_uncertain` | scan/point evidence is too weak for a hard decision |

Prediction-row verifier policy:

```text
point_subtype
```

OBB-only and no-soft variants remain ablations, not the main policy.

## Calibration Contract

Calibrated probability:

```text
p_geom_valid = P(geometry-consistent relation | geometry evidence)
```

Training source:

- `train_dev_calib` from official `3DSSG_subset` train-derived calibration rows;
- counterfactual negatives generated without using held-out prediction failures;
- held-out validation rows are not used to fit the calibrator.

Frozen calibrators:

| Calibrator | Path | Role |
| --- | --- | --- |
| pooled | `artifacts/calibration/p_geom_valid_smoke/model.json` | main recall-first operating point |
| family-specific | `artifacts/calibration/p_geom_valid_family/model.json` | stricter violation-first operating point |

Dev metrics:

| Model | Brier | AUROC | AUPRC |
| --- | ---: | ---: | ---: |
| pooled `p_geom_valid` | 0.0495 | 0.9822 | 0.9735 |

Family-specific AUROC:

| Family | AUROC |
| --- | ---: |
| `support_contact` | 0.9831 |
| `proximity` | 1.0000 |
| `relative_vertical` | 0.9982 |

## Prediction Evaluation Protocol

Prediction source:

```text
VL-SAT / vlsat_closed_set
```

Primary metrics:

- `R@50`
- `R@100`
- `Violation@50`
- `Violation@100`
- delta versus `semantic_only`
- relative violation reduction versus `semantic_only`

Main conditions:

| Condition | Role |
| --- | --- |
| `semantic_only` | original reproduced `VL-SAT` ranking |
| `probabilistic_recalibrated` | semantic score multiplied by frozen pooled `p_geom_valid` |
| `rule_verified_point_subtype` | hard-filter diagnostic |
| `family_specific_p_geom_valid` | stricter family-specific operating point |

Control conditions:

| Condition | Purpose |
| --- | --- |
| `control_p_geom_valid_only` | geometry-only ranking control |
| `control_distance_only` | simple distance heuristic control |
| `control_shuffled_geometry` | breaks geometry identity while preserving distribution |
| `control_wrong_pair_geometry` | tests object-pair identity |

## Prediction Join Contract

Input artifacts:

| Artifact | Path |
| --- | --- |
| predictions | `artifacts/evaluation/vlsat_closed_set/hardened/predictions.jsonl` |
| ground truth | `artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl` |
| geometry verification | `artifacts/evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl` |

Join acceptance:

- preserve all prediction rows;
- attach geometry/verifier fields where in scope;
- retain missing-geometry reason codes;
- do not drop predictions outside H001 families;
- keep held-out scan scope fixed.

Hardened join result:

| Item | Count / Status |
| --- | ---: |
| prediction rows preserved | 673,816 / 673,816 |
| primary geometry-checkable rows | 155,496 |
| missing point evidence rows | 32,877 |
| status | `ready` |
| errors | 0 |

## Implementation Tools

Canonical tools:

- `src/geocalib/export_calibration.py`
- `src/geocalib/fit_calibration.py`
- `src/geocalib/fit_family_calibration.py`
- `src/geocalib/export_predictions.py`
- `src/geocalib/run_vlsat_dump.py`
- `src/geocalib/vlsat_dump_hook.py`
- `src/geocalib/join_predictions.py`
- `src/geocalib/evaluate_predictions.py`
- `src/geocalib/evaluate_gt_verifier.py`

Hypothesis-stage outputs are preserved under
`archive/hypothesis_records/hypothesis/.../artifacts/`. Paper-body experiment
outputs must be regenerated through Docker after experiment entry.
