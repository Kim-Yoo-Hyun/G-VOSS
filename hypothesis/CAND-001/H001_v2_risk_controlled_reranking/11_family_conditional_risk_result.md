# H001_v2 Family-Conditional Calibrated Risk

Last updated: 2026-06-24 KST

Status: `h001_v2_family_conditional_risk_selected`

## Purpose

This stage updates the H001_v2 direction from pooled risk-penalty tuning toward
family-conditional calibrated geometry risk. The key change is conceptual and
method-level:

```text
p_geom_valid_family(e) = C_{family(e)}(phi(g_e))
R_family(e) = -log p_geom_valid_family(e)
U_family(e) = log semantic_score(e) - R_family(e)
score_family(e) = semantic_score(e) * p_geom_valid_family(e)
```

The existing metric runner stores this condition as
`control_family_specific_p_geom_valid` because it was originally introduced as
an ablation/control. H001_v2 now treats the same frozen artifact as a
family-conditional calibrated-risk operating point, not as a geometry-control
baseline. Geometry-only, distance-only, shuffled-geometry, and wrong-pair
conditions remain the true nontriviality controls.

## Protocol

Inputs are read-only locked H001 artifacts:

```text
family calibrator:
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json

VL-SAT source metrics:
experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/metrics.json

Open3DSG source metrics:
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/metrics.json
```

The family-specific calibrator is trained only from train/dev calibration rows.
It does not use source semantic scores or held-out source metrics. Source
evaluation uses the same K grid as current H001:

```text
K = {5, 10, 20, 50, 100}
```

## Calibration Evidence

Family-specific calibration artifact:

```text
model_id = h001-p-geom-valid-family-v1
families = proximity, relative_vertical, support_contact
```

Dev metrics from `p_geom_valid_family/report.md`:

| Family | Rows | Brier | NLL | AUROC | AUPRC |
| --- | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 537 | 0.0526 | 0.1564 | 0.9831 | 0.9675 |
| `proximity` | 382 | 0.0009 | 0.0125 | 1.0000 | 1.0000 |
| `relative_vertical` | 274 | 0.0189 | 0.0671 | 0.9982 | 0.9989 |

Interpretation:

- The family-specific models are not source-metric tuned.
- The calibration quality supports treating `p_geom_valid_family` as a
  deployable family-conditional risk score.
- Because dev rows are limited and family priors differ, this should be framed
  as a calibrated operating point rather than a broad learned relation model.

## Source Metrics

### VL-SAT

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| `pooled_risk` (`semantic_score * p_geom_valid`) | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| `family_conditional_risk` (`semantic_score * p_geom_valid_family`) | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 |

Against pooled risk, family-conditional risk on VL-SAT:

- keeps recall essentially flat: Delta R@100 `-0.0005`.
- reduces violation consistently: Delta V@100 `-0.0071`.
- is best interpreted as a stricter violation-first operating point.

### Open3DSG

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| `pooled_risk` (`semantic_score * p_geom_valid`) | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| `family_conditional_risk` (`semantic_score * p_geom_valid_family`) | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 |

Against pooled risk, family-conditional risk on Open3DSG:

- improves recall at every K.
- reduces violation at every K.
- gives the strongest current H001_v2 evidence among fixed-threshold,
  pooled-lambda, and family-conditional variants.

## Judgment

Fact:

- The family-specific calibrator is already frozen from train/dev calibration
  rows and uses no held-out source metric tuning.
- VL-SAT and Open3DSG K-sweep source metrics already include this condition.
- Open3DSG family-conditional risk dominates pooled risk across K on both
  recall and violation.
- VL-SAT family-conditional risk is nearly recall-neutral and lowers violation
  relative to pooled risk, especially at high K.

Inference:

- This is a stronger H001_v2 method direction than fixed `tau*` thresholding or
  single pooled `lambda` selection.
- The defensible claim is not "another control works"; it is that geometry
  validity is predicate-family conditional, so a pooled risk score can be
  miscalibrated across support/contact, proximity, and vertical relations.
- `family_conditional_risk` can be treated as the H001_v2 candidate operating
  point while preserving the original H001 main `lambda=1` pooled score as the
  current paper baseline/result.

## Paper Boundary

No locked H001 source metrics are changed by this update.

Recommended wording if promoted:

```text
We additionally report a family-conditional calibrated-risk operating point,
where each relation family uses its own frozen geometry-validity calibrator.
This tests whether relation-level physical consistency should be calibrated
under a shared pooled risk model or under family-conditioned geometry semantics.
```

Do not describe this as a generic ablation control. The true controls remain
geometry-only, distance-only, shuffled-geometry, and wrong-pair geometry.

## Next

The paper-facing naming pass is complete:

- reported summaries now use `family_conditional_risk` for the frozen
  family-calibrator operating point;
- legacy metric JSON keys such as `control_family_specific_p_geom_valid` remain
  unchanged;
- pooled `probabilistic_recalibrated` remains the current H001 main score unless
  the paper is explicitly revised to promote family-conditional risk.

If continuing H001_v2, the next method-development option is a coverage-aware
extension that keeps missing, unsupported, and uncertain geometry as explicit
states rather than hiding them inside one risk score.
