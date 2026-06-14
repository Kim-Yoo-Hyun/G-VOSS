# H001 Bootstrap CI

Created at UTC: `2026-06-12T16:56:02.612897+00:00`
Status: `ready`
Bootstrap samples: `1000`
Seed: `20260526`

Subgraphs are resampled with replacement. Point estimates are recomputed from the same per-subgraph contributions used for the bootstrap and checked against the locked metrics JSON.

| source | condition | K | R@K point | R@K 95% CI | V@K point | V@K 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| vlsat_closed_set_full_validation | semantic_only | 5 | 41.94% | [39.57%, 44.36%] | 0.29% | [0.07%, 0.55%] | n/a | n/a |
| vlsat_closed_set_full_validation | semantic_only | 10 | 63.22% | [60.17%, 66.20%] | 0.82% | [0.51%, 1.19%] | n/a | n/a |
| vlsat_closed_set_full_validation | semantic_only | 20 | 80.74% | [77.79%, 83.72%] | 1.42% | [1.12%, 1.72%] | n/a | n/a |
| vlsat_closed_set_full_validation | semantic_only | 50 | 92.72% | [90.56%, 94.83%] | 2.68% | [2.40%, 2.97%] | n/a | n/a |
| vlsat_closed_set_full_validation | semantic_only | 100 | 96.35% | [94.63%, 97.96%] | 4.76% | [4.44%, 5.09%] | n/a | n/a |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 5 | 41.54% | [39.33%, 43.82%] | 0.15% | [0.04%, 0.29%] | -0.40 pp | -0.15 pp |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 10 | 63.22% | [60.11%, 66.25%] | 0.71% | [0.46%, 1.04%] | +0.00 pp | -0.11 pp |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 20 | 81.07% | [78.23%, 83.94%] | 1.20% | [0.95%, 1.46%] | +0.33 pp | -0.23 pp |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 50 | 93.05% | [90.89%, 95.14%] | 2.29% | [2.03%, 2.54%] | +0.33 pp | -0.38 pp |
| vlsat_closed_set_full_validation | probabilistic_recalibrated | 100 | 96.88% | [95.33%, 98.32%] | 4.04% | [3.75%, 4.31%] | +0.53 pp | -0.72 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 5 | 41.97% | [39.57%, 44.38%] | 0.00% | [0.00%, 0.00%] | +0.03 pp | -0.29 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 10 | 63.17% | [60.10%, 66.18%] | 0.00% | [0.00%, 0.00%] | -0.05 pp | -0.82 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 20 | 80.74% | [77.79%, 83.69%] | 0.00% | [0.00%, 0.00%] | +0.00 pp | -1.42 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 50 | 92.57% | [90.44%, 94.69%] | 0.00% | [0.00%, 0.00%] | -0.15 pp | -2.68 pp |
| vlsat_closed_set_full_validation | rule_verified_point_subtype | 100 | 96.27% | [94.65%, 97.81%] | 0.00% | [0.00%, 0.00%] | -0.08 pp | -4.76 pp |
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 5 | 41.62% | [39.36%, 44.05%] | 0.11% | [0.00%, 0.26%] | -0.33 pp | -0.18 pp |
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 10 | 63.09% | [60.01%, 66.27%] | 0.51% | [0.31%, 0.77%] | -0.13 pp | -0.31 pp |
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 20 | 80.87% | [77.97%, 83.78%] | 1.09% | [0.84%, 1.34%] | +0.13 pp | -0.34 pp |
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 50 | 92.88% | [90.71%, 94.94%] | 2.06% | [1.84%, 2.28%] | +0.15 pp | -0.61 pp |
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 100 | 96.83% | [95.31%, 98.22%] | 3.33% | [3.08%, 3.57%] | +0.48 pp | -1.43 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 5 | 3.68% | [3.09%, 4.34%] | 51.31% | [48.79%, 53.65%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 10 | 10.02% | [8.92%, 11.16%] | 32.55% | [30.98%, 34.18%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 20 | 19.91% | [18.22%, 21.76%] | 20.88% | [19.93%, 21.81%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 50 | 40.96% | [38.49%, 43.59%] | 13.86% | [13.28%, 14.47%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | semantic_only | 100 | 51.61% | [49.10%, 54.28%] | 12.42% | [11.98%, 12.83%] | n/a | n/a |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 5 | 8.26% | [7.28%, 9.22%] | 6.28% | [5.11%, 7.52%] | +4.58 pp | -45.04 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 10 | 15.81% | [14.43%, 17.35%] | 6.99% | [6.15%, 7.90%] | +5.79 pp | -25.57 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 20 | 26.03% | [24.21%, 27.83%] | 6.54% | [5.93%, 7.16%] | +6.12 pp | -14.34 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 50 | 39.75% | [37.78%, 41.72%] | 6.06% | [5.67%, 6.47%] | -1.21 pp | -7.80 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | probabilistic_recalibrated | 100 | 57.23% | [54.86%, 59.52%] | 8.11% | [7.74%, 8.51%] | +5.61 pp | -4.31 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 5 | 7.07% | [6.25%, 7.94%] | 0.00% | [0.00%, 0.00%] | +3.40 pp | -51.31 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 10 | 13.14% | [11.89%, 14.36%] | 0.00% | [0.00%, 0.00%] | +3.12 pp | -32.55 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 20 | 24.22% | [22.40%, 26.13%] | 0.00% | [0.00%, 0.00%] | +4.31 pp | -20.88 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 50 | 42.95% | [40.53%, 45.49%] | 0.00% | [0.00%, 0.00%] | +1.99 pp | -13.86 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | rule_verified_point_subtype | 100 | 53.68% | [51.11%, 56.26%] | 0.00% | [0.00%, 0.00%] | +2.06 pp | -12.42 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | control_family_specific_p_geom_valid | 5 | 9.84% | [8.79%, 10.90%] | 4.20% | [3.25%, 5.18%] | +6.17 pp | -47.12 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | control_family_specific_p_geom_valid | 10 | 19.21% | [17.48%, 21.06%] | 4.82% | [4.03%, 5.60%] | +9.19 pp | -27.74 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | control_family_specific_p_geom_valid | 20 | 32.91% | [30.76%, 35.23%] | 4.41% | [3.89%, 4.95%] | +12.99 pp | -16.47 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | control_family_specific_p_geom_valid | 50 | 46.58% | [44.41%, 48.82%] | 2.86% | [2.55%, 3.18%] | +5.61 pp | -11.00 pp |
| open3dsg_ov_full_validation_recovery_relaxed_views_min2 | control_family_specific_p_geom_valid | 100 | 60.47% | [58.10%, 62.94%] | 3.41% | [3.07%, 3.77%] | +8.86 pp | -9.01 pp |

## Warnings

- none
