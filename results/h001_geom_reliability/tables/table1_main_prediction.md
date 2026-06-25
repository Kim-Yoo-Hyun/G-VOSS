# Table 1 Full-Validation VL-SAT Controlled-Anchor Result

| condition | role | r50 | r100 | violation50 | violation100 | delta_r50_vs_semantic | delta_r100_vs_semantic | delta_violation50_vs_semantic | delta_violation100_vs_semantic | relative_violation_reduction50 | relative_violation_reduction100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| semantic_only | full-validation reproduced VL-SAT semantic ranking | 0.9272 | 0.9635 | 0.0268 | 0.0476 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | 0.0000 | 0.0000 |
| probabilistic_recalibrated | pooled calibrated-risk ablation; semantic score times pooled p_geom_valid | 0.9305 | 0.9688 | 0.0229 | 0.0404 | +0.0033 | +0.0053 | -0.0038 | -0.0072 | 0.1432 | 0.1513 |
| rule_verified_point_subtype | hard-filter zero-violation diagnostic | 0.9257 | 0.9627 | 0.0000 | 0.0000 | -0.0015 | -0.0008 | -0.0268 | -0.0476 | 1.0000 | 1.0000 |
| family_conditional_risk | GeoCalib main score; semantic score times family-conditioned p_geom_valid | 0.9288 | 0.9683 | 0.0206 | 0.0333 | +0.0015 | +0.0048 | -0.0061 | -0.0143 | 0.2292 | 0.3010 |
