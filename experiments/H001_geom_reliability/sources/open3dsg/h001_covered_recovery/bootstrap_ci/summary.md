# H001 Bootstrap CI

Created at UTC: `2026-06-05T18:08:03.913969+00:00`
Status: `ready`
Bootstrap samples: `1000`
Seed: `20260526`

Subgraphs are resampled with replacement. Point estimates are recomputed from the same per-subgraph contributions used for the bootstrap and checked against the locked metrics JSON.

| source | condition | K | R@K point | R@K 95% CI | V@K point | V@K 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| vlsat_closed_set | semantic_only | 50 | 95.99% | [94.81%, 96.96%] | 2.47% | [2.19%, 2.80%] | n/a | n/a |
| vlsat_closed_set | semantic_only | 100 | 98.94% | [98.45%, 99.40%] | 4.69% | [4.34%, 5.06%] | n/a | n/a |
| vlsat_closed_set | probabilistic_recalibrated | 50 | 96.42% | [95.34%, 97.33%] | 2.34% | [2.06%, 2.63%] | +0.43 pp | -0.14 pp |
| vlsat_closed_set | probabilistic_recalibrated | 100 | 99.21% | [98.87%, 99.53%] | 3.91% | [3.61%, 4.24%] | +0.28 pp | -0.78 pp |
| vlsat_closed_set | rule_verified_point_subtype | 50 | 95.87% | [94.69%, 96.85%] | 0.00% | [0.00%, 0.00%] | -0.12 pp | -2.47 pp |
| vlsat_closed_set | rule_verified_point_subtype | 100 | 98.90% | [98.50%, 99.30%] | 0.00% | [0.00%, 0.00%] | -0.04 pp | -4.69 pp |
| vlsat_closed_set | control_family_specific_p_geom_valid | 50 | 96.19% | [95.07%, 97.13%] | 2.04% | [1.78%, 2.29%] | +0.20 pp | -0.44 pp |
| vlsat_closed_set | control_family_specific_p_geom_valid | 100 | 99.14% | [98.75%, 99.49%] | 3.10% | [2.83%, 3.38%] | +0.20 pp | -1.59 pp |
| open3dsg_ov_h001_r2_388 | semantic_only | 50 | 39.72% | [36.99%, 42.44%] | 13.31% | [12.65%, 14.01%] | n/a | n/a |
| open3dsg_ov_h001_r2_388 | semantic_only | 100 | 49.90% | [46.71%, 53.14%] | 11.99% | [11.48%, 12.55%] | n/a | n/a |
| open3dsg_ov_h001_r2_388 | probabilistic_recalibrated | 50 | 38.70% | [36.13%, 41.30%] | 5.94% | [5.49%, 6.44%] | -1.02 pp | -7.37 pp |
| open3dsg_ov_h001_r2_388 | probabilistic_recalibrated | 100 | 56.07% | [53.09%, 59.20%] | 8.11% | [7.67%, 8.55%] | +6.17 pp | -3.88 pp |
| open3dsg_ov_h001_r2_388 | rule_verified_point_subtype | 50 | 41.77% | [39.08%, 44.60%] | 0.00% | [0.00%, 0.00%] | +2.04 pp | -13.31 pp |
| open3dsg_ov_h001_r2_388 | rule_verified_point_subtype | 100 | 52.65% | [49.29%, 55.87%] | 0.00% | [0.00%, 0.00%] | +2.75 pp | -11.99 pp |
| open3dsg_ov_h001_r2_388 | control_family_specific_p_geom_valid | 50 | 45.58% | [42.81%, 48.45%] | 2.54% | [2.19%, 2.88%] | +5.85 pp | -10.77 pp |
| open3dsg_ov_h001_r2_388 | control_family_specific_p_geom_valid | 100 | 60.12% | [57.04%, 63.58%] | 3.23% | [2.86%, 3.62%] | +10.22 pp | -8.75 pp |

## Warnings

- none
