# Table 1 Main Held-Out Prediction Result

| condition | role | r50 | r100 | violation50 | violation100 | delta_r50_vs_semantic | delta_r100_vs_semantic | delta_violation50_vs_semantic | delta_violation100_vs_semantic | relative_violation_reduction50 | relative_violation_reduction100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| semantic_only | reproduced VL-SAT semantic ranking | 0.9599 | 0.9894 | 0.0247 | 0.0469 | +0.0000 | +0.0000 | +0.0000 | +0.0000 | 0.0000 | 0.0000 |
| probabilistic_recalibrated | main recall-first H001 condition | 0.9642 | 0.9921 | 0.0234 | 0.0391 | +0.0043 | +0.0028 | -0.0014 | -0.0078 | 0.0563 | 0.1666 |
| rule_verified_point_subtype | hard-filter zero-violation diagnostic | 0.9587 | 0.9890 | 0.0000 | 0.0000 | -0.0012 | -0.0004 | -0.0247 | -0.0469 | 1.0000 | 1.0000 |
| family_specific_p_geom_valid | stricter violation-first operating point | 0.9619 | 0.9914 | 0.0204 | 0.0310 | +0.0020 | +0.0020 | -0.0044 | -0.0159 | 0.1771 | 0.3381 |
