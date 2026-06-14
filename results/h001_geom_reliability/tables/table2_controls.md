# Table 2 Full-Validation VL-SAT Nontriviality Controls

| condition | purpose | r50 | r100 | violation50 | violation100 | delta_r50_vs_main | delta_violation50_vs_main |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_p_geom_valid_only | geometry-only ranking control | 0.2110 | 0.5184 | 0.0661 | 0.0711 | -0.7195 | +0.0431 |
| control_distance_only | simple distance heuristic control | 0.3746 | 0.5554 | 0.0724 | 0.0981 | -0.5559 | +0.0495 |
| control_shuffled_geometry | breaks geometry identity while preserving distribution | 0.8890 | 0.9494 | 0.0295 | 0.0588 | -0.0415 | +0.0065 |
| control_wrong_pair_geometry | tests object-pair identity | 0.8915 | 0.9529 | 0.0320 | 0.0601 | -0.0390 | +0.0091 |
| control_family_specific_p_geom_valid | stricter family-specific calibration | 0.9288 | 0.9683 | 0.0206 | 0.0333 | -0.0018 | -0.0023 |
