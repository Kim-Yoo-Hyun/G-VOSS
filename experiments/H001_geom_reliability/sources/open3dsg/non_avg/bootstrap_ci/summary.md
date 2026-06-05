# H001 Bootstrap CI

Created at UTC: `2026-06-04T11:42:33.050054+00:00`
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
| open3dsg_ov_non_avg | semantic_only | 50 | 43.10% | [40.38%, 45.93%] | 13.95% | [13.28%, 14.66%] | n/a | n/a |
| open3dsg_ov_non_avg | semantic_only | 100 | 53.20% | [49.96%, 56.56%] | 12.56% | [12.04%, 13.08%] | n/a | n/a |
| open3dsg_ov_non_avg | probabilistic_recalibrated | 50 | 39.45% | [37.13%, 41.64%] | 5.70% | [5.25%, 6.18%] | -3.65 pp | -8.25 pp |
| open3dsg_ov_non_avg | probabilistic_recalibrated | 100 | 56.39% | [53.59%, 59.37%] | 7.82% | [7.38%, 8.27%] | +3.18 pp | -4.74 pp |
| open3dsg_ov_non_avg | rule_verified_point_subtype | 50 | 45.07% | [42.38%, 47.94%] | 0.00% | [0.00%, 0.00%] | +1.96 pp | -13.95 pp |
| open3dsg_ov_non_avg | rule_verified_point_subtype | 100 | 54.81% | [51.64%, 58.13%] | 0.00% | [0.00%, 0.00%] | +1.61 pp | -12.56 pp |
| open3dsg_ov_non_avg | control_family_specific_p_geom_valid | 50 | 47.50% | [44.87%, 50.27%] | 2.43% | [2.14%, 2.74%] | +4.40 pp | -11.52 pp |
| open3dsg_ov_non_avg | control_family_specific_p_geom_valid | 100 | 60.47% | [57.59%, 63.80%] | 3.10% | [2.72%, 3.48%] | +7.27 pp | -9.46 pp |

## Warnings

- none
