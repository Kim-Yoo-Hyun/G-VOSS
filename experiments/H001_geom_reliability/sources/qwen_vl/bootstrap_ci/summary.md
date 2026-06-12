# H001 Bootstrap CI

Created at UTC: `2026-06-11T02:59:53.389036+00:00`
Status: `ready`
Bootstrap samples: `1000`
Seed: `20260526`

Subgraphs are resampled with replacement. Point estimates are recomputed from the same per-subgraph contributions used for the bootstrap and checked against the locked metrics JSON.

| source | condition | K | R@K point | R@K 95% CI | V@K point | V@K 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen_vl_semantic_source | semantic_only | 50 | 26.84% | [24.40%, 29.30%] | 12.39% | [11.80%, 12.93%] | n/a | n/a |
| qwen_vl_semantic_source | semantic_only | 100 | 35.80% | [32.81%, 38.61%] | 12.60% | [12.11%, 13.06%] | n/a | n/a |
| qwen_vl_semantic_source | probabilistic_recalibrated | 50 | 30.92% | [28.16%, 33.48%] | 7.87% | [7.34%, 8.40%] | +4.09 pp | -4.52 pp |
| qwen_vl_semantic_source | probabilistic_recalibrated | 100 | 36.54% | [33.50%, 39.50%] | 11.67% | [11.15%, 12.16%] | +0.75 pp | -0.93 pp |
| qwen_vl_semantic_source | rule_verified_point_subtype | 50 | 29.04% | [26.66%, 31.53%] | 0.00% | [0.00%, 0.00%] | +2.20 pp | -12.39 pp |
| qwen_vl_semantic_source | rule_verified_point_subtype | 100 | 36.31% | [33.27%, 39.18%] | 0.00% | [0.00%, 0.00%] | +0.51 pp | -12.60 pp |
| qwen_vl_semantic_source | control_family_specific_p_geom_valid | 50 | 33.08% | [30.13%, 35.81%] | 4.99% | [4.39%, 5.63%] | +6.25 pp | -7.40 pp |
| qwen_vl_semantic_source | control_family_specific_p_geom_valid | 100 | 36.54% | [33.52%, 39.47%] | 11.06% | [10.47%, 11.67%] | +0.75 pp | -1.54 pp |

## Warnings

- none
