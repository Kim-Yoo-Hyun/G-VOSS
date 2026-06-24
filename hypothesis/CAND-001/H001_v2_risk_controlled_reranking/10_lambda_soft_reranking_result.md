# H001_v2 Lambda-Soft Reranking Result

Last updated: 2026-06-24 KST

Status: `h001_v2_lambda_soft_diagnostic_locked`

## Protocol

This stage tests an actual H001_v2 soft-combination variant:

```text
score_lambda(e) = semantic_score(e) * p_geom_valid(e)^lambda
```

The lambda value is fixed before source evaluation.

Selection rule:

```text
lambda* = argmin_lambda NLL(y_geom_valid, p_geom_valid^lambda)
```

Selection input:

```text
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/scores.jsonl
role == dev
```

Source metrics are not read during lambda selection. `role == train` rows are
diagnostic only.

## Selected Lambda

Artifact:

```text
artifacts/calibration_lambda_selection/
```

Result:

```text
lambda* = 1.25
selection_rows = 1193
selection_mean_nll = 0.176239
selection_mean_brier = 0.049314
selection_accuracy_at_0_5 = 0.943839
diagnostic_train_mean_nll = 0.172779
```

Interpretation:

- The calibration dev objective prefers a slightly stronger geometry-risk
  penalty than the current `lambda=1` GeoCalib score.
- This selection is independent of VL-SAT/Open3DSG source metrics.

## Source Metrics

Artifacts:

```text
artifacts/source_eval_lambda/vlsat_full_validation/
artifacts/source_eval_lambda/open3dsg_recovery_relaxed_views_min2/
```

### VL-SAT

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| `probabilistic_recalibrated` (`lambda=1`) | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| `h001_v2_lambda_soft_reranking` (`lambda=1.25`) | 0.4126 | 0.6312 | 0.8107 | 0.9308 | 0.9690 | 0.0018 | 0.0069 | 0.0118 | 0.0222 | 0.0400 |
| `control_shuffled_geometry_lambda` | 0.3092 | 0.4758 | 0.6674 | 0.8661 | 0.9436 | 0.0073 | 0.0095 | 0.0141 | 0.0307 | 0.0622 |
| `control_wrong_pair_geometry_lambda` | 0.3069 | 0.4859 | 0.6903 | 0.8749 | 0.9441 | 0.0084 | 0.0106 | 0.0144 | 0.0337 | 0.0635 |

Against `lambda=1`, `lambda=1.25` is essentially flat on VL-SAT:

- R@5/R@10 drop slightly.
- R@20 is unchanged.
- R@50/R@100 improve by about `+0.00025`.
- V@50/V@100 improve slightly, but V@5 is slightly worse.

### Open3DSG

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| `probabilistic_recalibrated` (`lambda=1`) | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| `h001_v2_lambda_soft_reranking` (`lambda=1.25`) | 0.0811 | 0.1553 | 0.2555 | 0.3900 | 0.5627 | 0.0580 | 0.0666 | 0.0619 | 0.0610 | 0.0820 |
| `control_shuffled_geometry_lambda` | 0.0242 | 0.0488 | 0.0728 | 0.1390 | 0.2518 | 0.2934 | 0.2387 | 0.2157 | 0.2089 | 0.2019 |
| `control_wrong_pair_geometry_lambda` | 0.0144 | 0.0292 | 0.0498 | 0.1073 | 0.2306 | 0.2146 | 0.1889 | 0.1972 | 0.2084 | 0.2008 |

Against `lambda=1`, `lambda=1.25` is mixed on Open3DSG:

- V@5/V@10/V@20 improve by `-0.0047/-0.0033/-0.0036`.
- R@5/R@10/R@20/R@50/R@100 all drop.
- V@50/V@100 are slightly worse.

## Controls

The shuffled-geometry and wrong-pair-geometry lambda controls are much worse
than the real-geometry lambda condition on both sources. This supports that the
lambda-soft score is using object-pair geometry signal, not only changing score
scale or source-rank capacity.

## Judgment

Fact:

- The lambda selection protocol is implemented and uses calibration dev rows
  only.
- `lambda*=1.25` is selected by dev NLL over `p_geom_valid^lambda`.
- VL-SAT and Open3DSG source metrics are generated for K=`{5,10,20,50,100}`.
- Corrupted-geometry lambda controls are generated for both sources.

Inference:

- `lambda=1.25` is principled and geometry-specific, but it does not clearly
  dominate the current `lambda=1` GeoCalib score.
- The result is not strong enough to replace the current H001/GeoCalib main
  table.
- The current paper should keep `lambda=1` as the main reported
  `probabilistic_recalibrated` operating point and describe it as the deployed
  risk-aware soft reranking instance.
- `lambda=1.25` can be retained as H001_v2 diagnostic evidence that a
  calibration-selected stronger risk penalty yields a plausible but mixed
  recall-violation tradeoff.

## Next

No immediate main-paper promotion.

The next defensible direction is not a single pooled lambda. The
family-specific route has since been formalized as
`family_conditional_risk` in `11_family_conditional_risk_result.md`, because
the pooled `lambda=1.25` tradeoff differs by source and K. The remaining
optional extension is coverage-aware reporting/scoring.
