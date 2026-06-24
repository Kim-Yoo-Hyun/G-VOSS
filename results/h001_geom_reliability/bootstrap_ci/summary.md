# H001 Bootstrap CI

Created at UTC: `2026-05-26T09:20:35.278762+00:00`
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
| vlsat_closed_set | family_conditional_risk | 50 | 96.19% | [95.07%, 97.13%] | 2.04% | [1.78%, 2.29%] | +0.20 pp | -0.44 pp |
| vlsat_closed_set | family_conditional_risk | 100 | 99.14% | [98.75%, 99.49%] | 3.10% | [2.83%, 3.38%] | +0.20 pp | -1.59 pp |
| open3dsg_ov | semantic_only | 50 | 39.45% | [36.98%, 42.32%] | 13.26% | [12.61%, 13.96%] | n/a | n/a |
| open3dsg_ov | semantic_only | 100 | 49.63% | [46.59%, 52.71%] | 11.95% | [11.40%, 12.51%] | n/a | n/a |
| open3dsg_ov | probabilistic_recalibrated | 50 | 38.43% | [36.00%, 40.80%] | 5.75% | [5.26%, 6.24%] | -1.02 pp | -7.52 pp |
| open3dsg_ov | probabilistic_recalibrated | 100 | 55.80% | [52.98%, 58.87%] | 8.03% | [7.56%, 8.49%] | +6.17 pp | -3.92 pp |
| open3dsg_ov | rule_verified_point_subtype | 50 | 41.49% | [38.88%, 44.32%] | 0.00% | [0.00%, 0.00%] | +2.04 pp | -13.26 pp |
| open3dsg_ov | rule_verified_point_subtype | 100 | 52.38% | [49.23%, 55.47%] | 0.00% | [0.00%, 0.00%] | +2.75 pp | -11.95 pp |
| open3dsg_ov | family_conditional_risk | 50 | 45.30% | [42.68%, 48.28%] | 2.28% | [1.99%, 2.61%] | +5.85 pp | -10.99 pp |
| open3dsg_ov | family_conditional_risk | 100 | 59.84% | [56.75%, 63.15%] | 3.11% | [2.74%, 3.48%] | +10.22 pp | -8.84 pp |

## Warnings

- none
