# H001 / GeoCalib Geometry Reliability Report

Last updated: 2026-06-25 KST

This compact report is the paper-facing full-validation summary. The older
127-scan H001 outputs are historical/sensitivity evidence only and should not
be used as the current main table.

## Scoring Decision

- Main GeoCalib score: `family_conditional_risk =
  semantic_score * p_geom_valid_family`.
- Pooled calibrated-risk ablation: `probabilistic_recalibrated =
  semantic_score * p_geom_valid`.
- Geometry-only control: `control_p_geom_valid_only`, ranking by `p_geom_valid`
  without semantic score.
- Rule-verified variant: zero-violation diagnostic, not the default method.

## Full-Validation Evidence

Paper-facing scope: VL-SAT full official validation plus Open3DSG
full-validation `recovery_relaxed_views_min2/`. The measured denominator is
3,972 in-scope GT relations across `support_contact`, `proximity`, and
`relative_vertical`.

### VL-SAT Controlled Anchor

| condition | R@50 | R@100 | V@50 | V@100 | role |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.9272 | 0.9635 | 0.0268 | 0.0476 | reproduced source ranking |
| `family_conditional_risk` | 0.9288 | 0.9683 | 0.0206 | 0.0333 | GeoCalib main score |
| `probabilistic_recalibrated` | 0.9305 | 0.9688 | 0.0229 | 0.0404 | pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | 0.9257 | 0.9627 | 0.0000 | 0.0000 | zero-violation diagnostic |

### Open3DSG Full-Validation Recovery

| condition | R@50 | R@100 | V@50 | V@100 | role |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.4096 | 0.5161 | 0.1386 | 0.1242 | source ranking |
| `family_conditional_risk` | 0.4658 | 0.6047 | 0.0286 | 0.0341 | GeoCalib main score |
| `probabilistic_recalibrated` | 0.3975 | 0.5723 | 0.0606 | 0.0811 | pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | 0.4295 | 0.5368 | 0.0000 | 0.0000 | zero-violation diagnostic |

## Controls And Uncertainty

- VL-SAT geometry-only control reaches R@100/V@100 `0.5184/0.0711`, so
  geometry alone does not explain the result.
- VL-SAT distance-only control reaches R@100/V@100 `0.5554/0.0981`.
- VL-SAT shuffled/wrong-pair controls have higher V@100
  `0.0588/0.0601`, supporting the object-pair identity join.
- Full-validation bootstrap summary is mirrored in
  `bootstrap_ci/summary.md`; `family_conditional_risk` is the paper-facing
  GeoCalib main score.
- Open3DSG `family_conditional_risk` vs `semantic_only`: R@100 delta
  `+8.86 pp` with 95% CI `[+6.69,+10.96]`, V@100 delta `-9.01 pp` with
  95% CI `[-9.49,-8.53]`.
- VL-SAT `family_conditional_risk` vs `semantic_only`: R@100 delta
  `+0.48 pp` with 95% CI `[+0.11,+0.93]`, V@100 delta `-1.43 pp` with
  95% CI `[-1.60,-1.28]`.

## Claim Boundary

Allowed: scoped relation-reliability evidence for geometry-checkable 3D Scene
Graph relation families under explicit recall/violation tradeoffs.

Blocked: broad open-vocabulary 3DSSG generation improvement, Open3DSG
leaderboard/SOTA reproduction, arbitrary-source generality, or downstream task
improvement.

Open3DSG caveats to preserve: selected official non-averaged checkpoint,
filtered train/dev provenance, exact-label denominator, 548/548 recovery-policy
branch, 533/548 covered branch as sensitivity evidence, and residual
calibration risk.
