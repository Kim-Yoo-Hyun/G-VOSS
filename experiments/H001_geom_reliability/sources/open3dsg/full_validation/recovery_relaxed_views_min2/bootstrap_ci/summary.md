# H001 Bootstrap CI

Created at UTC: `2026-06-04T18:20:45.272707+00:00`
Status: `ready`
Bootstrap samples: `1000`
Seed: `20260526`

Subgraphs are resampled with replacement. Point estimates are recomputed from the same per-subgraph contributions used for the bootstrap and checked against the locked metrics JSON.

| source | condition | K | R@K point | R@K 95% CI | V@K point | V@K 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| vlsat_closed_set_full_validation | semantic_only | 50 | 92.72% | [90.56%, 94.83%] | 2.68% | [2.40%, 2.97%] | n/a | n/a |
| vlsat_closed_set_full_validation | semantic_only | 100 | 96.35% | [94.63%, 97.96%] | 4.76% | [4.44%, 5.09%] | n/a | n/a |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 50 | 93.05% | [90.89%, 95.14%] | 2.29% | [2.03%, 2.54%] | +0.33 pp | -0.38 pp |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 100 | 96.88% | [95.33%, 98.32%] | 4.04% | [3.75%, 4.31%] | +0.53 pp | -0.72 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 50 | 92.57% | [90.44%, 94.69%] | 0.00% | [0.00%, 0.00%] | -0.15 pp | -2.68 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 100 | 96.27% | [94.65%, 97.81%] | 0.00% | [0.00%, 0.00%] | -0.08 pp | -4.76 pp |
| vlsat_closed_set_full_validation | family_conditional_risk | 50 | 92.88% | [90.71%, 94.94%] | 2.06% | [1.84%, 2.28%] | +0.15 pp | -0.61 pp |
| vlsat_closed_set_full_validation | family_conditional_risk | 100 | 96.83% | [95.31%, 98.22%] | 3.33% | [3.08%, 3.57%] | +0.48 pp | -1.43 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 50 | 40.96% | [38.49%, 43.59%] | 13.86% | [13.28%, 14.47%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 100 | 51.61% | [49.10%, 54.28%] | 12.42% | [11.98%, 12.83%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 50 | 39.75% | [37.78%, 41.72%] | 6.06% | [5.67%, 6.47%] | -1.21 pp | -7.80 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 100 | 57.23% | [54.86%, 59.52%] | 8.11% | [7.74%, 8.51%] | +5.61 pp | -4.31 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 50 | 42.95% | [40.53%, 45.49%] | 0.00% | [0.00%, 0.00%] | +1.99 pp | -13.86 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 100 | 53.68% | [51.11%, 56.26%] | 0.00% | [0.00%, 0.00%] | +2.06 pp | -12.42 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | family_conditional_risk | 50 | 46.58% | [44.41%, 48.82%] | 2.86% | [2.55%, 3.18%] | +5.61 pp | -11.00 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | family_conditional_risk | 100 | 60.47% | [58.10%, 62.94%] | 3.41% | [3.07%, 3.77%] | +8.86 pp | -9.01 pp |

## Warnings

- none
