# H001 Bootstrap CI

Created at UTC: `2026-06-04T12:03:29.320995+00:00`
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
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 50 | 92.88% | [90.71%, 94.94%] | 2.06% | [1.84%, 2.28%] | +0.15 pp | -0.61 pp |
| vlsat_closed_set_full_validation | control_family_specific_p_geom_valid | 100 | 96.83% | [95.31%, 98.22%] | 3.33% | [3.08%, 3.57%] | +0.48 pp | -1.43 pp |

## Warnings

- none
