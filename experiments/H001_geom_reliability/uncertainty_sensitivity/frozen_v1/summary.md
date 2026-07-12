# H001 Uncertainty Sensitivity

Status: `ready_frozen_verifier_uncertainty_sensitivity`

`violation_all` is the reported verifier V with uncertain rows in the denominator; `violation_decidable` conditions on satisfied/violated rows; `pessimistic_violation` counts every uncertain row as a violation.

## K=100 diagnostic

| source | condition | V-all | V-decidable | uncertain | pessimistic V | decidable coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| vlsat_closed_set | semantic_only | 0.0476 | 0.0729 | 0.3464 | 0.3941 | 0.6536 |
| vlsat_closed_set | family_conditional_risk | 0.0333 | 0.0485 | 0.3127 | 0.3460 | 0.6873 |
| vlsat_closed_set | pooled_calibration | 0.0404 | 0.0594 | 0.3189 | 0.3594 | 0.6811 |
| vlsat_closed_set | geometry_only_family | 0.0224 | 0.0270 | 0.1715 | 0.1938 | 0.8285 |
| vlsat_closed_set | rank_average_fusion | 0.0259 | 0.0349 | 0.2584 | 0.2843 | 0.7416 |
| vlsat_closed_set | reciprocal_rank_fusion | 0.0251 | 0.0327 | 0.2337 | 0.2588 | 0.7663 |
| open3dsg_ov_recovery | semantic_only | 0.1242 | 0.2128 | 0.4164 | 0.5406 | 0.5836 |
| open3dsg_ov_recovery | family_conditional_risk | 0.0341 | 0.0457 | 0.2539 | 0.2880 | 0.7461 |
| open3dsg_ov_recovery | pooled_calibration | 0.0811 | 0.1145 | 0.2913 | 0.3724 | 0.7087 |
| open3dsg_ov_recovery | geometry_only_family | 0.0333 | 0.0425 | 0.2153 | 0.2486 | 0.7847 |
| open3dsg_ov_recovery | rank_average_fusion | 0.0532 | 0.0743 | 0.2834 | 0.3367 | 0.7166 |
| open3dsg_ov_recovery | reciprocal_rank_fusion | 0.0789 | 0.1098 | 0.2821 | 0.3609 | 0.7179 |
| sgfn_official_full_l160 | semantic_only | 0.0630 | 0.1005 | 0.3732 | 0.4362 | 0.6268 |
| sgfn_official_full_l160 | family_conditional_risk | 0.0381 | 0.0577 | 0.3396 | 0.3777 | 0.6604 |
| sgfn_official_full_l160 | pooled_calibration | 0.0488 | 0.0745 | 0.3451 | 0.3939 | 0.6549 |
| sgfn_official_full_l160 | geometry_only_family | 0.0224 | 0.0270 | 0.1715 | 0.1938 | 0.8285 |
| sgfn_official_full_l160 | rank_average_fusion | 0.0277 | 0.0383 | 0.2760 | 0.3037 | 0.7240 |
| sgfn_official_full_l160 | reciprocal_rank_fusion | 0.0284 | 0.0384 | 0.2602 | 0.2886 | 0.7398 |

All intervals and paired deltas use the same 1,000 subgraph-bootstrap indices within each source. This analysis does not change any score, rank, family, or verifier status.
