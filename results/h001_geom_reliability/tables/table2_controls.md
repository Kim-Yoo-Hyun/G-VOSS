# Table 2 Full-Validation VL-SAT Nontriviality Controls

| condition | purpose | r50 | r100 | violation50 | violation100 | delta_r50_vs_main | delta_violation50_vs_main |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_p_geom_valid_only | geometry-only ranking control; p_geom_valid without semantic score | 0.2110 | 0.5184 | 0.0661 | 0.0711 | -0.7178 | +0.0454 |
| control_distance_only | simple distance heuristic control | 0.3746 | 0.5554 | 0.0724 | 0.0981 | -0.5541 | +0.0518 |
| control_shuffled_geometry | breaks geometry identity while preserving distribution | 0.8890 | 0.9494 | 0.0295 | 0.0588 | -0.0398 | +0.0088 |
| control_wrong_pair_geometry | tests object-pair identity | 0.8915 | 0.9529 | 0.0320 | 0.0601 | -0.0373 | +0.0114 |
