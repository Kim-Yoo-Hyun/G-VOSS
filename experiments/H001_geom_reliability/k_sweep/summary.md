# H001 Low-K Top-Rank Diagnostic

Created at UTC: `2026-06-12T16:57:26+00:00`
Status: `ready`

## Protocol

- Fixed K grid: `5, 10, 20, 50, 100`.
- `K=1` is excluded from paper-metric consideration because it is too noisy.
- Low-K metrics are diagnostic until explicitly promoted after result review.
- Existing `metrics/` outputs are not overwritten; this report reads `metrics_k_sweep/`.

## Validation

- `K=50/100` point estimates, denominators, selected counts, and geometry coverage match the locked `metrics/` outputs.
- Bootstrap point estimates match `metrics_k_sweep/metrics.json` for all reported K values.

## Main-Candidate Gate

| condition | K | violation reduction both sources | recall delta >= -5 pp both sources | candidate |
| --- | ---: | --- | --- | --- |
| probabilistic | 10 | true | true | true |
| probabilistic | 20 | true | true | true |
| family_specific | 10 | true | true | true |
| family_specific | 20 | true | true | true |
| rule | 10 | true | true | true |
| rule | 20 | true | true | true |

## K-Sweep Metrics

| source | condition | K | R@K | V@K | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| VL-SAT full-validation | semantic | 5 | 41.94 | 0.29 | +0.00 | +0.00 |
| VL-SAT full-validation | semantic | 10 | 63.22 | 0.82 | +0.00 | +0.00 |
| VL-SAT full-validation | semantic | 20 | 80.74 | 1.42 | +0.00 | +0.00 |
| VL-SAT full-validation | semantic | 50 | 92.72 | 2.68 | +0.00 | +0.00 |
| VL-SAT full-validation | semantic | 100 | 96.35 | 4.76 | +0.00 | +0.00 |
| VL-SAT full-validation | probabilistic | 5 | 41.54 | 0.15 | -0.40 | -0.15 |
| VL-SAT full-validation | probabilistic | 10 | 63.22 | 0.71 | +0.00 | -0.11 |
| VL-SAT full-validation | probabilistic | 20 | 81.07 | 1.20 | +0.33 | -0.23 |
| VL-SAT full-validation | probabilistic | 50 | 93.05 | 2.29 | +0.33 | -0.38 |
| VL-SAT full-validation | probabilistic | 100 | 96.88 | 4.04 | +0.53 | -0.72 |
| VL-SAT full-validation | rule | 5 | 41.97 | 0.00 | +0.03 | -0.29 |
| VL-SAT full-validation | rule | 10 | 63.17 | 0.00 | -0.05 | -0.82 |
| VL-SAT full-validation | rule | 20 | 80.74 | 0.00 | +0.00 | -1.42 |
| VL-SAT full-validation | rule | 50 | 92.57 | 0.00 | -0.15 | -2.68 |
| VL-SAT full-validation | rule | 100 | 96.27 | 0.00 | -0.08 | -4.76 |
| VL-SAT full-validation | family_specific | 5 | 41.62 | 0.11 | -0.33 | -0.18 |
| VL-SAT full-validation | family_specific | 10 | 63.09 | 0.51 | -0.13 | -0.31 |
| VL-SAT full-validation | family_specific | 20 | 80.87 | 1.09 | +0.13 | -0.34 |
| VL-SAT full-validation | family_specific | 50 | 92.88 | 2.06 | +0.15 | -0.61 |
| VL-SAT full-validation | family_specific | 100 | 96.83 | 3.33 | +0.48 | -1.43 |
| Open3DSG recovery full-validation | semantic | 5 | 3.68 | 51.31 | +0.00 | +0.00 |
| Open3DSG recovery full-validation | semantic | 10 | 10.02 | 32.55 | +0.00 | +0.00 |
| Open3DSG recovery full-validation | semantic | 20 | 19.91 | 20.88 | +0.00 | +0.00 |
| Open3DSG recovery full-validation | semantic | 50 | 40.96 | 13.86 | +0.00 | +0.00 |
| Open3DSG recovery full-validation | semantic | 100 | 51.61 | 12.42 | +0.00 | +0.00 |
| Open3DSG recovery full-validation | probabilistic | 5 | 8.26 | 6.28 | +4.58 | -45.04 |
| Open3DSG recovery full-validation | probabilistic | 10 | 15.81 | 6.99 | +5.79 | -25.57 |
| Open3DSG recovery full-validation | probabilistic | 20 | 26.03 | 6.54 | +6.12 | -14.34 |
| Open3DSG recovery full-validation | probabilistic | 50 | 39.75 | 6.06 | -1.21 | -7.80 |
| Open3DSG recovery full-validation | probabilistic | 100 | 57.23 | 8.11 | +5.61 | -4.31 |
| Open3DSG recovery full-validation | rule | 5 | 7.07 | 0.00 | +3.40 | -51.31 |
| Open3DSG recovery full-validation | rule | 10 | 13.14 | 0.00 | +3.12 | -32.55 |
| Open3DSG recovery full-validation | rule | 20 | 24.22 | 0.00 | +4.31 | -20.88 |
| Open3DSG recovery full-validation | rule | 50 | 42.95 | 0.00 | +1.99 | -13.86 |
| Open3DSG recovery full-validation | rule | 100 | 53.68 | 0.00 | +2.06 | -12.42 |
| Open3DSG recovery full-validation | family_specific | 5 | 9.84 | 4.20 | +6.17 | -47.12 |
| Open3DSG recovery full-validation | family_specific | 10 | 19.21 | 4.82 | +9.19 | -27.74 |
| Open3DSG recovery full-validation | family_specific | 20 | 32.91 | 4.41 | +12.99 | -16.47 |
| Open3DSG recovery full-validation | family_specific | 50 | 46.58 | 2.86 | +5.61 | -11.00 |
| Open3DSG recovery full-validation | family_specific | 100 | 60.47 | 3.41 | +8.86 | -9.01 |

## Artifacts

- CSV: `experiments/H001_geom_reliability/k_sweep/recall_violation_curve.csv`
- SVG: `experiments/H001_geom_reliability/k_sweep/recall_violation_curve.svg`
