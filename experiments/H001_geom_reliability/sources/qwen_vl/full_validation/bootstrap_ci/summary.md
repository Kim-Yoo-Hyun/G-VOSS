# H001 Bootstrap CI

Created at UTC: `2026-06-11T18:16:30.430377+00:00`
Status: `ready`
Bootstrap samples: `1000`
Seed: `20260526`

Subgraphs are resampled with replacement. Point estimates are recomputed from the same per-subgraph contributions used for the bootstrap and checked against the locked metrics JSON.

| source | condition | K | R@K point | R@K 95% CI | V@K point | V@K 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen_vl_full_validation_semantic_source | semantic_only | 50 | 28.15% | [26.21%, 30.29%] | 12.26% | [11.80%, 12.73%] | n/a | n/a |
| qwen_vl_full_validation_semantic_source | semantic_only | 100 | 36.00% | [33.71%, 38.40%] | 12.46% | [12.04%, 12.84%] | n/a | n/a |
| qwen_vl_full_validation_semantic_source | probabilistic_recalibrated | 50 | 32.15% | [30.13%, 34.39%] | 7.95% | [7.51%, 8.35%] | +4.00 pp | -4.31 pp |
| qwen_vl_full_validation_semantic_source | probabilistic_recalibrated | 100 | 36.53% | [34.24%, 39.03%] | 11.66% | [11.22%, 12.03%] | +0.53 pp | -0.80 pp |
| qwen_vl_full_validation_semantic_source | rule_verified_point_subtype | 50 | 30.09% | [28.18%, 32.30%] | 0.00% | [0.00%, 0.00%] | +1.94 pp | -12.26 pp |
| qwen_vl_full_validation_semantic_source | rule_verified_point_subtype | 100 | 36.30% | [34.04%, 38.75%] | 0.00% | [0.00%, 0.00%] | +0.30 pp | -12.46 pp |
| qwen_vl_full_validation_semantic_source | control_family_specific_p_geom_valid | 50 | 33.79% | [31.67%, 36.09%] | 5.10% | [4.59%, 5.56%] | +5.64 pp | -7.16 pp |
| qwen_vl_full_validation_semantic_source | control_family_specific_p_geom_valid | 100 | 36.53% | [34.25%, 39.03%] | 11.13% | [10.65%, 11.58%] | +0.53 pp | -1.33 pp |

## Warnings

- none
